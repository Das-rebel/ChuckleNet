"""
LaughterRLTrainer: RL-based trainer for laughter prediction using XLM-R.

Workflow:
    1. Pretrain XLM-R with supervised CE loss (Phase 1)
    2. Collect human preferences on validation samples (Phase 2)
    3. Train reward model on preferences (Phase 3)
    4. PPO fine-tune actor with reward signal (Phase 4)
    5. Multi-objective evaluation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from transformers import AutoModel, AutoTokenizer, AutoConfig
from torch.utils.data import Dataset, DataLoader
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RLConfig:
    """Configuration for RL training pipeline."""
    model_name: str = "xlm-roberta-base"
    learning_rate: float = 2e-5
    ppo_clip_epsilon: float = 0.2
    kl_anneal_steps: int = 100
    reward_model_epochs: int = 3
    ppo_epochs: int = 5
    batch_size: int = 16
    gradient_accumulation: int = 4
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    max_seq_length: int = 512
    num_labels: int = 2
    hidden_dropout: float = 0.1
    reward_model_dim: int = 768
    value_head_dim: int = 256
    kl_beta_init: float = 0.1
    kl_beta_min: float = 0.01
    kl_anneal_type: str = "linear"  # linear, exponential, cosine
    save_dir: str = "./experiments/rl_checkpoints"
    log_interval: int = 10
    eval_interval: int = 500
    warmup_steps: int = 100


@dataclass
class LaughterState:
    """State representation for RL decision-making."""
    word_embedding: torch.Tensor  # [seq_len, 768]
    speaker_context: str  # "opening_joke" / "punchline"
    audience_response: float  # [-1, 1]
    cultural_background: str  # en / zh / hi
    prev_laughter_probs: List[float]  # Last N word probs
    duchenne_score: float  # [0, 1]
    incongruity_score: float  # [0, 1]
    tom_score: float  # [0, 1]

    def to_tensor(self) -> torch.Tensor:
        """Convert state to flattened tensor."""
        features = [
            self.word_embedding.mean(dim=0),  # [768]
            torch.tensor([1.0 if self.speaker_context == "punchline" else 0.0]),
            torch.tensor([self.audience_response]),
            torch.tensor([1.0 if self.cultural_background == "en" else 0.0,
                         1.0 if self.cultural_background == "zh" else 0.0,
                         1.0 if self.cultural_background == "hi" else 0.0]),
            torch.tensor(self.prev_laughter_probs[-5:] if len(self.prev_laughter_probs) >= 5
                        else self.prev_laughter_probs + [0.0] * (5 - len(self.prev_laughter_probs))),
            torch.tensor([self.duchenne_score, self.incongruity_score, self.tom_score]),
        ]
        return torch.cat(features)  # [783]

    @classmethod
    def from_batch(cls, word_embeddings: torch.Tensor, contexts: List[str],
                   responses: List[float], cultures: List[str],
                   prev_probs: List[List[float]], duchenne: List[float],
                   incongruity: List[float], tom: List[float]) -> List["LaughterState"]:
        """Create batch of states from flattened inputs."""
        states = []
        for i in range(word_embeddings.size(0)):
            states.append(cls(
                word_embedding=word_embeddings[i],
                speaker_context=contexts[i] if i < len(contexts) else "opening_joke",
                audience_response=responses[i] if i < len(responses) else 0.0,
                cultural_background=cultures[i] if i < len(cultures) else "en",
                prev_laughter_probs=prev_probs[i] if i < len(prev_probs) else [],
                duchenne_score=duchenne[i] if i < len(duchenne) else 0.0,
                incongunuity_score=incongruity[i] if i < len(incongruity) else 0.0,
                tom_score=tom[i] if i < len(tom) else 0.0,
            ))
        return states


@dataclass
class LaughterAction:
    """Action representation for laughter prediction."""
    laugh_label: int  # 0 or 1
    confidence: float  # [0, 1]
    laughter_type: str  # "micro" / "burst" / "solo" / "crowd"
    intensity: float  # 0.0 / 0.33 / 0.66 / 1.0

    def to_vector(self) -> torch.Tensor:
        """Convert action to vector representation."""
        type_map = {"micro": 0.0, "burst": 0.33, "solo": 0.66, "crowd": 1.0}
        return torch.tensor([
            float(self.laugh_label),
            self.confidence,
            type_map.get(self.laughter_type, 0.0),
            self.intensity,
        ])

    @classmethod
    def from_vector(cls, vector: torch.Tensor) -> "LaughterAction":
        """Parse action from vector representation."""
        type_map = {0.0: "micro", 0.33: "burst", 0.66: "solo", 1.0: "crowd"}
        nearest_type = min(type_map.keys(), key=lambda x: abs(x - vector[2].item()))
        return cls(
            laugh_label=int(vector[0].item() > 0.5),
            confidence=vector[1].item(),
            laughter_type=type_map[nearest_type],
            intensity=vector[3].item(),
        )


# =============================================================================
# Network Architectures
# =============================================================================

class LaughterActor(nn.Module):
    """
    XLM-R based policy network for laughter prediction.
    
    Outputs:
        - logits: [batch, 2] for laugh/no-laugh classification
        - confidence: [batch, 1] prediction confidence
        - laughter_type_logits: [batch, 4] for micro/burst/solo/crowd
        - intensity_logits: [batch, 4] for 0.0/0.33/0.66/1.0
    """

    def __init__(self, config: RLConfig):
        super().__init__()
        self.config = config
        self.encoder = AutoModel.from_pretrained(
            config.model_name,
            hidden_dropout_prob=config.hidden_dropout,
            attention_probs_dropout_prob=config.hidden_dropout,
        )
        self.hidden_size = self.encoder.config.hidden_size  # 768 for xlm-roberta-base

        # Classification head for laugh/no-laugh
        self.classifier = nn.Sequential(
            nn.Dropout(config.hidden_dropout),
            nn.Linear(self.hidden_size, 256),
            nn.GELU(),
            nn.Dropout(config.hidden_dropout),
            nn.Linear(256, 2),
        )

        # Confidence head
        self.confidence_head = nn.Sequential(
            nn.Dropout(config.hidden_dropout),
            nn.Linear(self.hidden_size, 128),
            nn.GELU(),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

        # Laughter type head (micro, burst, solo, crowd)
        self.laughter_type_head = nn.Sequential(
            nn.Dropout(config.hidden_dropout),
            nn.Linear(self.hidden_size, 128),
            nn.GELU(),
            nn.Linear(128, 4),
        )

        # Intensity head (0.0, 0.33, 0.66, 1.0)
        self.intensity_head = nn.Sequential(
            nn.Dropout(config.hidden_dropout),
            nn.Linear(self.hidden_size, 128),
            nn.GELU(),
            nn.Linear(128, 4),
        )

    def forward(self, input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None,
                **kwargs) -> Dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len]

        Returns:
            Dict with 'logits', 'confidence', 'laughter_type_logits', 'intensity_logits'
        """
        if attention_mask is None:
            attention_mask = (input_ids != self.config.tokenizer.pad_token_id).long()

        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # [batch, seq_len, 768]
        pooled_output = sequence_output.mean(dim=1)  # [batch, 768]

        logits = self.classifier(pooled_output)  # [batch, 2]
        confidence = self.confidence_head(pooled_output)  # [batch, 1]
        laughter_type_logits = self.laughter_type_head(pooled_output)  # [batch, 4]
        intensity_logits = self.intensity_head(pooled_output)  # [batch, 4]

        return {
            "logits": logits,
            "confidence": confidence,
            "laughter_type_logits": laughter_type_logits,
            "intensity_logits": intensity_logits,
            "pooled_output": pooled_output,
            "sequence_output": sequence_output,
        }

    def get_action(self, input_ids: torch.Tensor,
                   attention_mask: Optional[torch.Tensor] = None,
                   deterministic: bool = False) -> Tuple[LaughterAction, torch.Tensor]:
        """
        Sample action from policy.

        Returns:
            Tuple of (LaughterAction, log_prob)
        """
        outputs = self.forward(input_ids, attention_mask)
        logits = outputs["logits"]

        if deterministic:
            laugh_label = logits.argmax(dim=-1)
            log_prob = None
        else:
            dist = torch.distributions.Categorical(logits=logits)
            laugh_label = dist.sample()
            log_prob = dist.log_prob(laugh_label)

        confidence = outputs["confidence"].squeeze(-1)
        laughter_type_logits = outputs["laughter_type_logits"]
        intensity_logits = outputs["intensity_logits"]

        type_dist = torch.distributions.Categorical(logits=laughter_type_logits)
        intensity_dist = torch.distributions.Categorical(logits=intensity_logits)

        laughter_type_idx = type_dist.sample() if not deterministic else type_dist.argmax()
        intensity_idx = intensity_dist.sample() if not deterministic else intensity_dist.argmax()

        type_map = ["micro", "burst", "solo", "crowd"]
        intensity_values = [0.0, 0.33, 0.66, 1.0]

        action = LaughterAction(
            laugh_label=laugh_label.item(),
            confidence=confidence.mean().item(),
            laughter_type=type_map[laughter_type_idx.item()],
            intensity=intensity_values[intensity_idx.item()],
        )

        return action, log_prob

    def get_word_embeddings(self, input_ids: torch.Tensor,
                            attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Get per-word embeddings for state construction."""
        if attention_mask is None:
            attention_mask = (input_ids != self.config.tokenizer.pad_token_id).long()

        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        return outputs.last_hidden_state  # [batch, seq_len, 768]


class LaughterCritic(nn.Module):
    """
    Value estimator for PPO.
    
    Estimates V(s) - expected cumulative reward from current state.
    """

    def __init__(self, config: RLConfig):
        super().__init__()
        self.config = config
        self.encoder = AutoModel.from_pretrained(
            config.model_name,
            hidden_dropout_prob=config.hidden_dropout,
            attention_probs_dropout_prob=config.hidden_dropout,
        )
        self.hidden_size = self.encoder.config.hidden_size

        self.value_head = nn.Sequential(
            nn.Dropout(config.hidden_dropout),
            nn.Linear(self.hidden_size, config.value_head_dim),
            nn.GELU(),
            nn.Dropout(config.hidden_dropout),
            nn.Linear(config.value_head_dim, 1),
        )

    def forward(self, input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None,
                state_features: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute state value estimate.

        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len]
            state_features: Optional [batch, 783] additional state features

        Returns:
            value: [batch, 1]
        """
        if attention_mask is None:
            attention_mask = (input_ids != self.config.tokenizer.pad_token_id).long()

        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        pooled_output = sequence_output.mean(dim=1)  # [batch, 768]

        if state_features is not None:
            # Concatenate transformer output with state features
            combined = torch.cat([pooled_output, state_features], dim=-1)
            # Project to expected dimension
            combined = nn.functional.gelu(
                nn.Linear(768 + state_features.size(-1), 768)(combined)
            )
            value = self.value_head(combined)
        else:
            value = self.value_head(pooled_output)

        return value

    def get_value(self, input_ids: torch.Tensor,
                  attention_mask: Optional[torch.Tensor] = None,
                  state: Optional[LaughterState] = None) -> torch.Tensor:
        """Get scalar value for a state."""
        state_features = state.to_tensor().unsqueeze(0) if state is not None else None
        return self.forward(input_ids, attention_mask, state_features)


class RewardModel(nn.Module):
    """
    Reward model trained on human preferences.
    
    Uses Bradley-Terry model: P(preferred) = sigmoid(r(preferred) - r(disfavored))
    """

    def __init__(self, config: RLConfig):
        super().__init__()
        self.config = config
        self.encoder = AutoModel.from_pretrained(
            config.model_name,
            hidden_dropout_prob=config.hidden_dropout,
            attention_probs_dropout_prob=config.hidden_dropout,
        )
        self.hidden_size = self.encoder.config.hidden_size

        self.reward_head = nn.Sequential(
            nn.Dropout(config.hidden_dropout),
            nn.Linear(self.hidden_size, 256),
            nn.GELU(),
            nn.Dropout(config.hidden_dropout),
            nn.Linear(256, 1),
        )

    def forward(self, input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Compute reward for a prediction.

        Args:
            input_ids: [batch, seq_len]
            attention_mask: [batch, seq_len]

        Returns:
            reward: [batch, 1]
        """
        if attention_mask is None:
            attention_mask = (input_ids != self.config.tokenizer.pad_token_id).long()

        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state.mean(dim=1)
        reward = self.reward_head(pooled_output)
        return reward

    def compute_preference_loss(self, preferred_ids: torch.Tensor,
                                disfavored_ids: torch.Tensor,
                                preferred_mask: Optional[torch.Tensor] = None,
                                disfavored_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Bradley-Terry preference loss.

        P(preferred > disfavored) = sigmoid(r(preferred) - r(disfavored))
        """
        r_preferred = self.forward(preferred_ids, preferred_mask)
        r_disfavored = self.forward(disfavored_ids, disfavored_mask)

        diff = r_preferred - r_disfavored
        loss = -torch.log(torch.sigmoid(diff)).mean()
        return loss


# =============================================================================
# Reward Function
# =============================================================================

def compute_reward(prediction: Dict[str, Any],
                   ground_truth: Dict[str, Any],
                   state: LaughterState) -> float:
    """
    Multi-objective reward function for laughter prediction.

    Components:
        1. Base: accuracy (F1)
        2. Temporal coherence: laughs should cluster
        3. Intensity calibration: match expected distribution
        4. Cultural adaptability: per-language biases
        5. Asymmetric penalty: false positives > false negatives

    Args:
        prediction: Dict with 'laugh_label', 'confidence', 'laughter_type', 'intensity'
        ground_truth: Dict with 'laugh_label', 'laughter_type', 'intensity'
        state: Current LaughterState

    Returns:
        reward: float
    """
    pred_label = prediction.get("laugh_label", 0)
    gt_label = ground_truth.get("laugh_label", 0)

    # 1. Base accuracy reward
    if pred_label == gt_label:
        base_reward = 1.0 if gt_label == 1 else 0.5  # Weight positives more
    else:
        if gt_label == 1:
            base_reward = -0.5  # False negative
        else:
            base_reward = -1.0  # False positive (asymmetric penalty)

    # 2. Temporal coherence reward
    temporal_reward = 0.0
    if len(state.prev_laughter_probs) > 0:
        last_probs = state.prev_laughter_probs[-3:]
        avg_prev = sum(last_probs) / len(last_probs) if last_probs else 0.0
        # If previous words had high laugh probability, current should too
        if pred_label == 1 and avg_prev > 0.5:
            temporal_reward = 0.2
        elif pred_label == 0 and avg_prev < 0.2:
            temporal_reward = 0.1
        # Cluster breaking penalty
        elif pred_label != gt_label and gt_label == pred_label:
            pass  # Already handled
        elif pred_label == 0 and avg_prev > 0.7:
            temporal_reward = -0.1  # Breaking a cluster unexpectedly
        elif pred_label == 1 and avg_prev < 0.1:
            temporal_reward = -0.1  # Isolated laugh unlikely

    # 3. Intensity calibration
    intensity_reward = 0.0
    if pred_label == 1 and gt_label == 1:
        pred_intensity = prediction.get("intensity", 0.5)
        gt_intensity = ground_truth.get("intensity", 0.5)
        intensity_diff = abs(pred_intensity - gt_intensity)
        intensity_reward = 0.2 * (1.0 - intensity_diff)
    elif pred_label == 1:
        # Over-confident on intensity
        intensity_reward = -0.1 * prediction.get("intensity", 0.5)

    # 4. Cultural adaptability
    culture_reward = 0.0
    culture = state.cultural_background
    if culture == "zh":
        # Chinese audiences: subtler, shorter laughter
        if prediction.get("laughter_type") in ["micro", "solo"]:
            culture_reward = 0.1
        if pred_label == 1 and prediction.get("intensity", 0) > 0.7:
            culture_reward -= 0.1  # Penalize excessive intensity
    elif culture == "hi":
        # Hindi audiences: more expressive
        if prediction.get("laughter_type") in ["burst", "crowd"]:
            culture_reward = 0.1
    # English: neutral reward

    # 5. Asymmetric penalty for false positives
    # (Already handled in base_reward, this adds additional context)
    if pred_label == 1 and gt_label == 0:
        # Additional penalty for high-confidence false positives
        conf = prediction.get("confidence", 0.5)
        if conf > 0.8:
            base_reward -= 0.3

    total_reward = base_reward + temporal_reward + intensity_reward + culture_reward

    # Clamp reward
    return max(-2.0, min(2.0, total_reward))


# =============================================================================
# Preference Dataset
# =============================================================================

class PreferenceDataset(Dataset):
    """Dataset for human preference data."""

    def __init__(self, samples: List[Dict[str, Any]]):
        """
        Args:
            samples: List of dicts with 'input_ids_a', 'input_ids_b', 'preferred' (0 or 1)
        """
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]
        return {
            "input_ids_a": torch.tensor(sample["input_ids_a"], dtype=torch.long),
            "input_ids_b": torch.tensor(sample["input_ids_b"], dtype=torch.long),
            "preferred": torch.tensor(sample["preferred"], dtype=torch.long),
        }


# =============================================================================
# Main RL Trainer
# =============================================================================

class LaughterRLTrainer:
    """
    RL trainer for laughter prediction.

    Workflow:
        1. Pretrain XLM-R with supervised CE loss (Phase 1)
        2. Collect human preferences on validation samples (Phase 2)
        3. Train reward model on preferences (Phase 3)
        4. PPO fine-tune actor with reward signal (Phase 4)
        5. Multi-objective evaluation
    """

    def __init__(self, config: RLConfig):
        self.config = config
        self.device = config.device

        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        config.tokenizer = self.tokenizer

        # Initialize networks
        self.actor = LaughterActor(config).to(self.device)
        self.critic = LaughterCritic(config).to(self.device)
        self.reward_model = None  # Trained in Phase 3

        # Optimizers
        self.actor_optimizer = None
        self.critic_optimizer = None
        self.reward_optimizer = None

        # Training state
        self.global_step = 0
        self.kl_beta = config.kl_beta_init

        # Metrics tracking
        self.metrics_history = {
            "train_loss": [],
            "ppo_loss": [],
            "reward_loss": [],
            "eval_f1": [],
            "eval_precision": [],
            "eval_recall": [],
            "eval_iou_f1": [],
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logger

    def _build_optimizer(self, model: nn.Module,
                         learning_rate: Optional[float] = None) -> torch.optim.Optimizer:
        """Build optimizer with weight decay."""
        lr = learning_rate or self.config.learning_rate
        no_decay = ["bias", "LayerNorm.weight", "layernorm.weight"]
        params = [
            {
                "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
                "weight_decay": 0.01,
            },
            {
                "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
                "weight_decay": 0.0,
            },
        ]
        return torch.optim.AdamW(params, lr=lr)

    def _compute_kl_anneal(self, step: int) -> float:
        """Compute KL penalty coefficient with annealing."""
        if self.config.kl_anneal_type == "linear":
            frac = min(1.0, step / self.config.kl_anneal_steps)
            return self.config.kl_beta_init + frac * (self.config.kl_beta_min - self.config.kl_beta_init)
        elif self.config.kl_anneal_type == "exponential":
            decay = (self.config.kl_beta_min / self.config.kl_beta_init) ** (step / self.config.kl_anneal_steps)
            return self.config.kl_beta_init * decay + self.config.kl_beta_min * (1 - decay)
        elif self.config.kl_anneal_type == "cosine":
            import math
            frac = (1 + math.cos(math.pi * step / self.config.kl_anneal_steps)) / 2
            return self.config.kl_beta_min + frac * (self.config.kl_beta_init - self.config.kl_beta_min)
        else:
            return self.config.kl_beta_init

    def _tokenize_batch(self, texts: List[str]) -> Dict[str, torch.Tensor]:
        """Tokenize a batch of texts."""
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.config.max_seq_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].to(self.device),
            "attention_mask": encoded["attention_mask"].to(self.device),
        }

    # =========================================================================
    # Phase 1: Supervised Pretraining
    # =========================================================================

    def pretrain_supervised(self,
                            train_texts: List[str],
                            train_labels: List[int],
                            val_texts: List[str],
                            val_labels: List[int],
                            num_epochs: int = 5) -> Dict[str, List[float]]:
        """
        Phase 1: Supervised baseline training.

        Args:
            train_texts: List of training texts
            train_labels: List of binary labels (0/1)
            val_texts: List of validation texts
            val_labels: List of validation binary labels
            num_epochs: Number of training epochs

        Returns:
            Dict of training metrics
        """
        self.logger.info("Phase 1: Starting supervised pretraining")

        self.actor_optimizer = self._build_optimizer(self.actor)
        self.critic_optimizer = self._build_optimizer(self.critic)

        train_input_ids = self._tokenize_batch(train_texts)
        val_input_ids = self._tokenize_batch(val_texts)

        train_labels_tensor = torch.tensor(train_labels, dtype=torch.long).to(self.device)
        val_labels_tensor = torch.tensor(val_labels, dtype=torch.long).to(self.device)

        best_f1 = 0.0
        best_state = None

        for epoch in range(num_epochs):
            self.actor.train()
            epoch_losses = []

            # Mini-batch training
            batch_size = self.config.batch_size
            num_batches = (len(train_texts) + batch_size - 1) // batch_size

            for batch_idx in range(num_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(train_texts))

                batch_input_ids = train_input_ids["input_ids"][start_idx:end_idx]
                batch_attention_mask = train_input_ids["attention_mask"][start_idx:end_idx]
                batch_labels = train_labels_tensor[start_idx:end_idx]

                # Forward pass
                outputs = self.actor(batch_input_ids, batch_attention_mask)
                logits = outputs["logits"]

                # Cross-entropy loss
                ce_loss = F.cross_entropy(logits, batch_labels)

                # Loss with gradient accumulation
                loss = ce_loss / self.config.gradient_accumulation
                loss.backward()

                epoch_losses.append(ce_loss.item())

                if (batch_idx + 1) % self.config.gradient_accumulation == 0:
                    torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 1.0)
                    self.actor_optimizer.step()
                    self.actor_optimizer.zero_grad()
                    self.global_step += 1

                if self.global_step % self.config.log_interval == 0:
                    self.logger.info(
                        f"Epoch {epoch+1}/{num_epochs} | Batch {batch_idx+1}/{num_batches} | "
                        f"Loss: {ce_loss.item():.4f} | Step: {self.global_step}"
                    )

            # Validation
            val_metrics = self._evaluate(val_input_ids, val_labels_tensor)
            avg_loss = sum(epoch_losses) / len(epoch_losses)

            self.metrics_history["train_loss"].append(avg_loss)
            self.metrics_history["eval_f1"].append(val_metrics["f1"])

            self.logger.info(
                f"Epoch {epoch+1}/{num_epochs} complete | "
                f"Train Loss: {avg_loss:.4f} | "
                f"Val F1: {val_metrics['f1']:.4f} | "
                f"Val Precision: {val_metrics['precision']:.4f} | "
                f"Val Recall: {val_metrics['recall']:.4f}"
            )

            # Save best model
            if val_metrics["f1"] > best_f1:
                best_f1 = val_metrics["f1"]
                best_state = {
                    "actor": self.actor.state_dict(),
                    "critic": self.critic.state_dict(),
                    "actor_optimizer": self.actor_optimizer.state_dict(),
                    "epoch": epoch,
                    "f1": best_f1,
                }
                self.logger.info(f"New best F1: {best_f1:.4f}")

        # Restore best model
        if best_state is not None:
            self.actor.load_state_dict(best_state["actor"])
            self.critic.load_state_dict(best_state["critic"])
            self.logger.info(f"Restored best model with F1: {best_f1:.4f}")

        self.logger.info(f"Phase 1 complete. Best F1: {best_f1:.4f}")
        return {
            "train_loss": self.metrics_history["train_loss"],
            "eval_f1": self.metrics_history["eval_f1"],
            "best_f1": best_f1,
        }

    def _evaluate(self, input_ids: Dict[str, torch.Tensor],
                   labels: torch.Tensor) -> Dict[str, float]:
        """Run evaluation on a dataset."""
        self.actor.eval()
        all_preds = []
        all_probs = []

        with torch.no_grad():
            batch_size = self.config.batch_size
            num_samples = input_ids["input_ids"].size(0)

            for batch_idx in range(0, num_samples, batch_size):
                batch_ids = input_ids["input_ids"][batch_idx:batch_idx + batch_size]
                batch_mask = input_ids["attention_mask"][batch_idx:batch_idx + batch_size]

                outputs = self.actor(batch_ids, batch_mask)
                probs = F.softmax(outputs["logits"], dim=-1)
                preds = probs.argmax(dim=-1)

                all_preds.extend(preds.cpu().tolist())
                all_probs.extend(probs[:, 1].cpu().tolist())

        all_preds = torch.tensor(all_preds)
        all_probs = torch.tensor(all_probs)
        labels = labels[:len(all_preds)]

        # Compute metrics
        tp = ((all_preds == 1) & (labels == 1)).sum().item()
        fp = ((all_preds == 1) & (labels == 0)).sum().item()
        fn = ((all_preds == 0) & (labels == 1)).sum().item()
        tn = ((all_preds == 0) & (labels == 0)).sum().item()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # IoU-F1
        iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
        iou_f1 = 2 * iou / (iou + 1) if iou > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "iou_f1": iou_f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

    # =========================================================================
    # Phase 2: Collect Human Preferences
    # =========================================================================

    def collect_preferences(self,
                           samples: List[Dict[str, Any]],
                           human_evaluator) -> List[Dict[str, Any]]:
        """
        Phase 2: Collect preference data from humans.

        Args:
            samples: List of samples with 'text_a', 'text_b' pairs
            human_evaluator: Callable that takes (text_a, text_b) and returns 0 or 1
                            indicating which sample is preferred (0=a, 1=b)

        Returns:
            List of preference dicts with input_ids and labels
        """
        self.logger.info("Phase 2: Collecting human preferences")

        preferences = []
        for i, sample in enumerate(samples):
            text_a = sample["text_a"]
            text_b = sample["text_b"]

            # Tokenize
            encoded_a = self.tokenizer(text_a, truncation=True, max_length=self.config.max_seq_length)
            encoded_b = self.tokenizer(text_b, truncation=True, max_length=self.config.max_seq_length)

            # Get human preference
            preferred = human_evaluator(text_a, text_b)

            preferences.append({
                "input_ids_a": encoded_a["input_ids"],
                "input_ids_b": encoded_b["input_ids"],
                "preferred": preferred,
                "text_a": text_a,
                "text_b": text_b,
            })

            if (i + 1) % 50 == 0:
                self.logger.info(f"Collected {i+1}/{len(samples)} preferences")

        self.logger.info(f"Phase 2 complete. Collected {len(preferences)} preferences")
        return preferences

    # =========================================================================
    # Phase 3: Train Reward Model
    # =========================================================================

    def train_reward_model(self, preferences: List[Dict[str, Any]]) -> float:
        """
        Phase 3: Train reward model on preference data.

        Args:
            preferences: List of preference dicts from Phase 2

        Returns:
            Final reward model loss
        """
        self.logger.info("Phase 3: Training reward model")

        self.reward_model = RewardModel(self.config).to(self.device)
        self.reward_optimizer = self._build_optimizer(self.reward_model)

        dataset = PreferenceDataset(preferences)
        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            drop_last=False,
        )

        total_loss = 0.0
        num_batches = 0

        for epoch in range(self.config.reward_model_epochs):
            epoch_losses = []
            for batch in dataloader:
                preferred_ids = batch["input_ids_a"].to(self.device)
                disfavored_ids = batch["input_ids_b"].to(self.device)

                # Adjust for preferred label (if preferred=1, a is preferred; if preferred=0, b is preferred)
                # We need to handle this carefully
                a_preferred = []
                b_preferred = []
                for i, pref in enumerate(batch["preferred"]):
                    if pref.item() == 0:
                        a_preferred.append(preferred_ids[i])
                        b_preferred.append(disfavored_ids[i])
                    else:
                        b_preferred.append(preferred_ids[i])
                        a_preferred.append(disfavored_ids[i])

                # Compute loss with correct ordering
                loss = self.reward_model.compute_preference_loss(
                    preferred_ids=preferred_ids,
                    disfavored_ids=disfavored_ids,
                )

                self.reward_optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.reward_model.parameters(), 1.0)
                self.reward_optimizer.step()

                epoch_losses.append(loss.item())
                total_loss += loss.item()
                num_batches += 1

            avg_loss = sum(epoch_losses) / len(epoch_losses)
            self.metrics_history["reward_loss"].append(avg_loss)
            self.logger.info(f"Reward epoch {epoch+1}/{self.config.reward_model_epochs} | Loss: {avg_loss:.4f}")

        avg_final_loss = total_loss / num_batches
        self.logger.info(f"Phase 3 complete. Final loss: {avg_final_loss:.4f}")
        return avg_final_loss

    # =========================================================================
    # Phase 4: PPO Fine-tuning
    # =========================================================================

    def rl_finetune(self,
                    dataset_texts: List[str],
                    dataset_labels: List[int],
                    num_epochs: int = 5) -> Dict[str, List[float]]:
        """
        Phase 4: PPO fine-tuning of the actor.

        Args:
            dataset_texts: List of texts for fine-tuning
            dataset_labels: Ground truth labels
            num_epochs: Number of PPO epochs

        Returns:
            Dict of training metrics
        """
        self.logger.info("Phase 4: Starting PPO fine-tuning")

        if self.reward_model is None:
            raise ValueError("Reward model not trained. Run Phase 3 first.")

        self.actor.train()
        self.critic.train()
        self.reward_model.eval()

        ppo_losses = []
        actor_losses = []
        value_losses = []
        kl_losses = []

        for epoch in range(num_epochs):
            epoch_ppo_losses = []
            epoch_actor_losses = []
            epoch_value_losses = []
            epoch_kl_losses = []

            batch_size = self.config.batch_size
            num_batches = (len(dataset_texts) + batch_size - 1) // batch_size

            indices = np.random.permutation(len(dataset_texts))

            for batch_idx in range(num_batches):
                batch_start = batch_idx * batch_size
                batch_end = min(batch_start + batch_size, len(dataset_texts))
                batch_indices = indices[batch_start:batch_end]

                batch_texts = [dataset_texts[i] for i in batch_indices]
                batch_labels = [dataset_labels[i] for i in batch_indices]

                # Tokenize
                batch_input_ids = self._tokenize_batch(batch_texts)

                # Old policy (before update)
                with torch.no_grad():
                    old_outputs = self.actor(
                        batch_input_ids["input_ids"],
                        batch_input_ids["attention_mask"],
                    )
                    old_logits = old_outputs["logits"]
                    old_probs = F.softmax(old_logits, dim=-1)
                    old_log_probs = F.log_softmax(old_logits, dim=-1)

                # New policy
                new_outputs = self.actor(
                    batch_input_ids["input_ids"],
                    batch_input_ids["attention_mask"],
                )
                new_logits = new_outputs["logits"]
                new_probs = F.softmax(new_logits, dim=-1)
                new_log_probs = F.log_softmax(new_logits, dim=-1)

                # Value estimate
                values = self.critic(
                    batch_input_ids["input_ids"],
                    batch_input_ids["attention_mask"],
                )

                # Compute rewards using the reward model
                rewards = []
                for i, text in enumerate(batch_texts):
                    pred = {
                        "laugh_label": new_probs[i].argmax().item(),
                        "confidence": new_outputs["confidence"][i].item(),
                        "laughter_type": ["micro", "burst", "solo", "crowd"][
                            new_outputs["laughter_type_logits"][i].argmax().item()
                        ],
                        "intensity": [0.0, 0.33, 0.66, 1.0][
                            new_outputs["intensity_logits"][i].argmax().item()
                        ],
                    }
                    gt = {"laugh_label": batch_labels[i]}
                    # Dummy state for now
                    state = LaughterState(
                        word_embedding=new_outputs["sequence_output"][i].mean(dim=0),
                        speaker_context="punchline",
                        audience_response=0.0,
                        cultural_background="en",
                        prev_laughter_probs=[],
                        duchenne_score=0.5,
                        incongruity_score=0.5,
                        tom_score=0.5,
                    )
                    reward = compute_reward(pred, gt, state)
                    rewards.append(reward)

                rewards = torch.tensor(rewards).to(self.device).unsqueeze(-1)

                # PPO clipping
                ratio = new_probs / (old_probs + 1e-8)
                ratio = ratio.gather(1, old_logits.argmax(dim=-1, keepdim=True))

                clipped_ratio = torch.clamp(
                    ratio,
                    1 - self.config.ppo_clip_epsilon,
                    1 + self.config.ppo_clip_epsilon,
                )
                ppo_objective = torch.min(
                    ratio * rewards,
                    clipped_ratio * rewards,
                )

                # KL penalty
                kl = F.kl_div(
                    new_log_probs,
                    old_log_probs,
                    reduction="batchmean",
                )
                annealed_kl_beta = self._compute_kl_anneal(self.global_step)
                self.kl_beta = annealed_kl_beta

                # Total PPO loss
                ppo_loss = -ppo_objective.mean() + annealed_kl_beta * kl

                # Value loss (bootstrap from rewards)
                with torch.no_grad():
                    target_value = rewards
                value_loss = F.mse_loss(values, target_value)

                total_loss = ppo_loss + 0.5 * value_loss

                # Backward
                self.actor_optimizer.zero_grad()
                self.critic_optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
                torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
                self.actor_optimizer.step()
                self.critic_optimizer.step()

                self.global_step += 1

                epoch_ppo_losses.append(ppo_loss.item())
                epoch_actor_losses.append(-ppo_objective.mean().item())
                epoch_value_losses.append(value_loss.item())
                epoch_kl_losses.append(kl.item())

            avg_ppo = sum(epoch_ppo_losses) / len(epoch_ppo_losses)
            avg_actor = sum(epoch_actor_losses) / len(epoch_actor_losses)
            avg_value = sum(epoch_value_losses) / len(epoch_value_losses)
            avg_kl = sum(epoch_kl_losses) / len(epoch_kl_losses)

            ppo_losses.append(avg_ppo)
            actor_losses.append(avg_actor)
            value_losses.append(avg_value)
            kl_losses.append(avg_kl)

            self.logger.info(
                f"PPO Epoch {epoch+1}/{num_epochs} | "
                f"PPO Loss: {avg_ppo:.4f} | "
                f"Actor: {avg_actor:.4f} | "
                f"Value: {avg_value:.4f} | "
                f"KL: {avg_kl:.4f} | "
                f"β: {annealed_kl_beta:.4f}"
            )

        self.metrics_history["ppo_loss"] = ppo_losses

        self.logger.info("Phase 4 complete.")
        return {
            "ppo_loss": ppo_losses,
            "actor_loss": actor_losses,
            "value_loss": value_losses,
            "kl_loss": kl_losses,
        }

    # =========================================================================
    # Phase 5: Multi-Objective Evaluation
    # =========================================================================

    def evaluate(self,
                test_texts: List[str],
                test_labels: List[int],
                language_breakdown: bool = True) -> Dict[str, Any]:
        """
        Multi-objective evaluation.

        Args:
            test_texts: Test texts
            test_labels: Ground truth labels
            language_breakdown: If True, break down by language

        Returns:
            Dict with overall and per-language metrics
        """
        self.logger.info("Starting evaluation")

        test_input_ids = self._tokenize_batch(test_texts)
        test_labels_tensor = torch.tensor(test_labels, dtype=torch.long).to(self.device)

        overall = self._evaluate(test_input_ids, test_labels_tensor)

        results = {
            "overall": overall,
            "timestamp": datetime.now().isoformat(),
        }

        if language_breakdown and "language" in test_texts[0] if isinstance(test_texts[0], dict) else False:
            # Group by language if available
            lang_groups = {}
            for i, text in enumerate(test_texts):
                if isinstance(text, dict):
                    lang = text.get("language", "unknown")
                else:
                    lang = "unknown"

                if lang not in lang_groups:
                    lang_groups[lang] = {"texts": [], "labels": []}
                lang_groups[lang]["texts"].append(text if isinstance(text, str) else text.get("text", ""))
                lang_groups[lang]["labels"].append(test_labels[i])

            for lang, group in lang_groups.items():
                lang_input = self._tokenize_batch(group["texts"])
                lang_labels = torch.tensor(group["labels"], dtype=torch.long).to(self.device)
                lang_metrics = self._evaluate(lang_input, lang_labels)
                results[f"lang_{lang}"] = lang_metrics

        self.metrics_history["eval_f1"].append(overall["f1"])
        self.metrics_history["eval_precision"].append(overall["precision"])
        self.metrics_history["eval_recall"].append(overall["recall"])
        self.metrics_history["eval_iou_f1"].append(overall["iou_f1"])

        self.logger.info(
            f"Evaluation complete | "
            f"F1: {overall['f1']:.4f} | "
            f"Precision: {overall['precision']:.4f} | "
            f"Recall: {overall['recall']:.4f} | "
            f"IoU-F1: {overall['iou_f1']:.4f}"
        )

        return results

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def save_checkpoint(self, path: str) -> None:
        """Save trainer state to checkpoint."""
        checkpoint = {
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "reward_model": self.reward_model.state_dict() if self.reward_model else None,
            "actor_optimizer": self.actor_optimizer.state_dict() if self.actor_optimizer else None,
            "critic_optimizer": self.critic_optimizer.state_dict() if self.critic_optimizer else None,
            "reward_optimizer": self.reward_optimizer.state_dict() if self.reward_optimizer else None,
            "global_step": self.global_step,
            "kl_beta": self.kl_beta,
            "config": self.config,
            "metrics_history": self.metrics_history,
        }
        torch.save(checkpoint, path)
        self.logger.info(f"Checkpoint saved to {path}")

    def load_checkpoint(self, path: str) -> None:
        """Load trainer state from checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(checkpoint["actor"])
        self.critic.load_state_dict(checkpoint["critic"])
        if checkpoint["reward_model"] is not None:
            self.reward_model = RewardModel(self.config).to(self.device)
            self.reward_model.load_state_dict(checkpoint["reward_model"])
        if checkpoint["actor_optimizer"] is not None:
            self.actor_optimizer = self._build_optimizer(self.actor)
            self.actor_optimizer.load_state_dict(checkpoint["actor_optimizer"])
        if checkpoint["critic_optimizer"] is not None:
            self.critic_optimizer = self._build_optimizer(self.critic)
            self.critic_optimizer.load_state_dict(checkpoint["critic_optimizer"])
        if checkpoint["reward_optimizer"] is not None:
            self.reward_optimizer = self._build_optimizer(self.reward_model)
            self.reward_optimizer.load_state_dict(checkpoint["reward_optimizer"])
        self.global_step = checkpoint["global_step"]
        self.kl_beta = checkpoint["kl_beta"]
        self.metrics_history = checkpoint.get("metrics_history", self.metrics_history)
        self.logger.info(f"Checkpoint loaded from {path}")

    def get_metrics_history(self) -> Dict[str, List[float]]:
        """Get training metrics history."""
        return self.metrics_history


# =============================================================================
# Demo / Main
# =============================================================================

def main():
    """
    Demonstrate LaughterRLTrainer initialization and structure.
    """
    print("=" * 60)
    print("LaughterRLTrainer Demo")
    print("=" * 60)

    # Create config
    config = RLConfig(
        model_name="xlm-roberta-base",
        learning_rate=2e-5,
        ppo_clip_epsilon=0.2,
        kl_anneal_steps=100,
        reward_model_epochs=3,
        ppo_epochs=5,
        batch_size=8,  # Smaller for demo
        gradient_accumulation=2,  # Smaller for demo
        device="cuda" if torch.cuda.is_available() else "cpu",
        save_dir="./experiments/rl_demo",
    )

    print(f"\nConfig:")
    print(f"  Model: {config.model_name}")
    print(f"  Device: {config.device}")
    print(f"  Learning Rate: {config.learning_rate}")
    print(f"  PPO Clip Epsilon: {config.ppo_clip_epsilon}")
    print(f"  KL Anneal Steps: {config.kl_anneal_steps}")

    # Create trainer
    print("\nInitializing trainer...")
    trainer = LaughterRLTrainer(config)
    print(f"  Actor: {type(trainer.actor).__name__}")
    print(f"  Critic: {type(trainer.critic).__name__}")
    print(f"  Reward Model: {trainer.reward_model}")

    # Show actor architecture
    print("\nActor Architecture:")
    actor_params = sum(p.numel() for p in trainer.actor.parameters())
    print(f"  Total parameters: {actor_params:,}")

    print("\nCritic Architecture:")
    critic_params = sum(p.numel() for p in trainer.critic.parameters())
    print(f"  Total parameters: {critic_params:,}")

    # Demonstrate state and action
    print("\nState Example:")
    dummy_state = LaughterState(
        word_embedding=torch.randn(10, 768),
        speaker_context="punchline",
        audience_response=0.5,
        cultural_background="en",
        prev_laughter_probs=[0.8, 0.7, 0.9, 0.6, 0.7],
        duchenne_score=0.7,
        incongruity_score=0.6,
        tom_score=0.8,
    )
    state_tensor = dummy_state.to_tensor()
    print(f"  State tensor shape: {state_tensor.shape}")

    print("\nAction Example:")
    dummy_action = LaughterAction(
        laugh_label=1,
        confidence=0.85,
        laughter_type="burst",
        intensity=0.66,
    )
    action_vector = dummy_action.to_vector()
    print(f"  Action vector: {action_vector}")

    # Test reward computation
    print("\nReward Computation Example:")
    prediction = {
        "laugh_label": 1,
        "confidence": 0.85,
        "laughter_type": "burst",
        "intensity": 0.66,
    }
    ground_truth = {
        "laugh_label": 1,
        "laughter_type": "solo",
        "intensity": 0.5,
    }
    reward = compute_reward(prediction, ground_truth, dummy_state)
    print(f"  Reward: {reward:.4f}")

    # Run a forward pass (mock data)
    print("\nForward Pass Test:")
    mock_input = trainer._tokenize_batch(["Hello world, this is a test"])
    print(f"  Input shape: {mock_input['input_ids'].shape}")

    trainer.actor.eval()
    with torch.no_grad():
        outputs = trainer.actor(
            mock_input["input_ids"],
            mock_input["attention_mask"],
        )
    print(f"  Logits shape: {outputs['logits'].shape}")
    print(f"  Confidence: {outputs['confidence'].mean().item():.4f}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
