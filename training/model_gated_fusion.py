"""
Gated Multimodal Fusion: XLM-R (text) + WavLM (audio)
Late fusion with learnable gate that learns when to trust audio vs text.

Architecture:
    Text: XLM-R → mean_pool(768) → proj(768→256) → text_emb
    Audio: WavLM → mean_pool(768) → proj(768→256) → audio_emb
    Gate: concat([text_emb, audio_emb]) → sigmoid → g
    Fused: g * audio_emb + (1-g) * text_emb
    Classifier: fused → linear(256,128) → relu → dropout → linear(128,2)

Gate bias=-2.2 ensures initial g≈0.10 (90% text-leaning).
This prevents audio from being ignored before it learns meaningful representations.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from typing import Optional, Tuple


class GatedMultimodalFusion(nn.Module):
    """
    Gated late fusion for text and audio modalities.
    
    Gate learns to weight: g=0 (trust text) vs g=1 (trust audio).
    Bias initialization at -2.2 → initial g≈0.10 (text-leaning at start).
    """
    
    def __init__(
        self,
        text_dim: int = 768,
        audio_dim: int = 768,
        hidden_dim: int = 256,
        dropout: float = 0.2,
        gate_bias_init: float = -2.2,
    ):
        super().__init__()
        
        # Text projection
        self.text_proj = nn.Sequential(
            nn.Linear(text_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        
        # Audio projection
        self.audio_proj = nn.Sequential(
            nn.Linear(audio_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        
        # Gate network
        self.gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, 1),
        )
        
        # Initialize gate bias to make g≈0.10 at start
        with torch.no_grad():
            self.gate[0].bias.fill_(gate_bias_init)
        
        # Classifier head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 2),
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        text_emb: torch.Tensor,      # (batch, text_dim)
        audio_emb: torch.Tensor,     # (batch, audio_dim)
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            text_emb: (batch, 768) — XLM-R [CLS] or mean-pooled
            audio_emb: (batch, 768) — WavLM mean-pooled
        Returns:
            logits: (batch, 2)
            gate_value: (batch, 1) — for monitoring
        """
        # Project both modalities
        t = self.text_proj(text_emb)   # (batch, hidden_dim)
        a = self.audio_proj(audio_emb) # (batch, hidden_dim)
        
        # Compute gate
        gate_input = torch.cat([t, a], dim=-1)  # (batch, hidden_dim*2)
        gate_logit = self.gate(gate_input)        # (batch, 1)
        g = torch.sigmoid(gate_logit)             # (batch, 1), [0,1]
        
        # Fused representation: g*audio + (1-g)*text
        fused = g * a + (1 - g) * t               # (batch, hidden_dim)
        fused = self.dropout(fused)
        
        # Classification
        logits = self.classifier(fused)           # (batch, 2)
        
        return logits, g


class WavLMXLMRFusionModel(nn.Module):
    """
    Full model: XLM-R text encoder + WavLM audio encoder + Gated fusion.
    
    In training:
        - Phase 1 (text baseline): Train XLM-R only, freeze audio
        - Phase 2 (frozen fusion): Freeze XLM-R, train audio_proj + gate
        - Phase 3 (joint): Unfreeze top-2 XLM-R layers, train all
    """
    
    def __init__(
        self,
        xlmr_name: str = "xlm-roberta-base",
        wavlm_name: str = "microsoft/wavlm-base-plus",
        text_hidden_dim: int = 256,
        audio_hidden_dim: int = 256,
        dropout: float = 0.2,
        gate_bias_init: float = -2.2,
        freeze_text: bool = True,
        freeze_audio: bool = True,
    ):
        super().__init__()
        
        # Text encoder (XLM-R)
        from transformers import AutoModel, AutoTokenizer
        self.xlmr = AutoModel.from_pretrained(xlmr_name)
        self.text_hidden_dim = self.xlmr.config.hidden_size  # 768
        
        # Audio encoder (WavLM)
        from transformers import AutoModel as WavLMModel
        self.wavlm = WavLMModel.from_pretrained(wavlm_name)
        self.audio_hidden_dim = self.wavlm.config.hidden_size  # 768
        
        # Gated fusion
        self.fusion = GatedMultimodalFusion(
            text_dim=self.text_hidden_dim,
            audio_dim=self.audio_hidden_dim,
            hidden_dim=text_hidden_dim,
            dropout=dropout,
            gate_bias_init=gate_bias_init,
        )
        
        # Freeze flags (actual freezing done in training loop)
        self.freeze_text = freeze_text
        self.freeze_audio = freeze_audio
        
        # For phase 2: which layers to freeze/unfreeze
        self._xlmr_freeze_layers = []  # populated in freeze_params()
    
    def freeze_params(self, freeze_text: bool = True, freeze_audio: bool = True):
        """Freeze text and/or audio encoders."""
        if freeze_text:
            for param in self.xlmr.parameters():
                param.requires_grad = False
        
        if freeze_audio:
            for param in self.wavlm.parameters():
                param.requires_grad = False
    
    def unfreeze_xlmr_top_n(self, n: int = 2):
        """Unfreeze top n layers of XLM-R for joint fine-tuning."""
        # xlm-roberta-base has 12 layers (0-11)
        # Unfreeze last n layers
        for layer_idx in range(12 - n, 12):
            for param in self.xlmr.encoder.layer[layer_idx].parameters():
                param.requires_grad = True
    
    def get_trainable_params(self):
        """Return trainable parameters grouped by learning rate."""
        params = []
        
        # XLM-R (usually frozen in phases 1-2)
        xlmr_params = [p for p in self.xlmr.parameters() if p.requires_grad]
        if xlmr_params:
            params.append(("xlmr", xlmr_params, 5e-5))
        
        # WavLM
        wavlm_params = [p for p in self.wavlm.parameters() if p.requires_grad]
        if wavlm_params:
            params.append(("wavlm", wavlm_params, 1e-3))
        
        # Fusion (always trainable)
        fusion_params = [p for p in self.fusion.parameters() if p.requires_grad]
        params.append(("fusion", fusion_params, 1e-3))
        
        return params
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        audio_input: torch.Tensor,      # (batch, seq_len) raw audio waveform
        audio_sample_rate: int = 16000,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            input_ids: (batch, seq_len) — XLM-R token IDs
            attention_mask: (batch, seq_len)
            audio_input: (batch, audio_len) — raw audio waveforms
            audio_sample_rate: 16000
        Returns:
            logits: (batch, 2)
            gate_values: (batch, 1)
        """
        # Text encoding
        text_outputs = self.xlmr(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        text_emb = text_outputs.last_hidden_state[:, 0, :]  # [CLS] (batch, 768)
        
        # Audio encoding
        audio_outputs = self.wavlm(audio_input)
        # Mean pool over time: (batch, T, 768) → (batch, 768)
        audio_emb = audio_outputs.last_hidden_state.mean(dim=1)
        
        # Gated fusion
        logits, gate_values = self.fusion(text_emb, audio_emb)
        
        return logits, gate_values


# ─── Per-Phase Configuration ───────────────────────────────────────────────────

PHASE_CONFIGS = {
    "phase1_text_baseline": {
        "freeze_text": False,  # Train XLM-R
        "freeze_audio": True,  # Frozen
        "unfreeze_xlmr_layers": 0,  # Full fine-tune
        "lr_text": 5e-5,
        "lr_audio": 0,  # frozen
        "lr_fusion": 0,  # frozen
        "epochs": 5,
        "description": "Text-only baseline, no audio",
    },
    "phase2_frozen_fusion": {
        "freeze_text": True,  # Freeze XLM-R
        "freeze_audio": False,  # Train WavLM
        "unfreeze_xlmr_layers": 0,
        "lr_text": 0,
        "lr_audio": 1e-3,
        "lr_fusion": 1e-3,
        "epochs": 10,
        "description": "Audio learns complement, text frozen",
    },
    "phase3_joint": {
        "freeze_text": True,  # Keep XLM-R frozen (or partially unfrozen below)
        "freeze_audio": False,
        "unfreeze_xlmr_layers": 2,  # Unfreeze last 2 layers
        "lr_text": 2e-5,
        "lr_audio": 5e-4,
        "lr_fusion": 5e-4,
        "epochs": 5,
        "description": "Joint fine-tune, target F1 > 0.85",
    },
}


def create_model_for_phase(phase: str, **kwargs) -> WavLMXLMRFusionModel:
    """Create model and configure for specific training phase."""
    config = PHASE_CONFIGS[phase]
    
    model = WavLMXLMRFusionModel(**kwargs)
    model.freeze_params(
        freeze_text=config["freeze_text"],
        freeze_audio=config["freeze_audio"],
    )
    
    if config["unfreeze_xlmr_layers"] > 0:
        model.unfreeze_xlmr_top_n(config["unfreeze_xlmr_layers"])
    
    return model