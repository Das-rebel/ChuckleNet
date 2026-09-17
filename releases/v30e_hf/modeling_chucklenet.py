"""ChuckleNet v30e: lightweight laughter head over mean-pooled WavLM embeddings.

The checkpoint is *not* a raw-audio model. Expected input is a 768-d
WavLM-base last-hidden-state embedding (typically mean-pooled over time).
"""

import torch
from torch import nn
from transformers import AutoConfig, AutoModelForAudioClassification, PretrainedConfig, PreTrainedModel


class ChuckleNetConfig(PretrainedConfig):
    model_type = "chucklenet"

    def __init__(
        self,
        in_dim=768,
        hidden=256,
        hidden2=128,
        dropout1=0.3,
        dropout2=0.2,
        threshold=0.75,
        sample_rate=16000,
        base_model_name="subhajitdas/wavlm-base-mirror",
        **kwargs,
    ):
        self.in_dim = in_dim
        self.hidden = hidden
        self.hidden2 = hidden2
        self.dropout1 = dropout1
        self.dropout2 = dropout2
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.base_model_name = base_model_name
        super().__init__(**kwargs)


class ChuckleNetDetector(PreTrainedModel):
    config_class = ChuckleNetConfig
    base_model_prefix = "chucklenet"

    def __init__(self, config: ChuckleNetConfig):
        super().__init__(config)
        self.net = nn.Sequential(
            nn.Linear(config.in_dim, config.hidden),
            nn.ReLU(),
            nn.Dropout(config.dropout1),
            nn.Linear(config.hidden, config.hidden2),
            nn.ReLU(),
            nn.Dropout(config.dropout2),
            nn.Linear(config.hidden2, 1),
        )
        self.post_init()

    def forward(self, wavlm_embedding=None, input_features=None, **kwargs):
        """Return laughter logits with shape [batch].

        Accepts `wavlm_embedding` as the primary input; `input_features` is
        accepted as an alias for generic HF pipelines/integrations.
        """
        x = wavlm_embedding if wavlm_embedding is not None else input_features
        if x is None:
            raise ValueError("Provide a [batch, 768] WavLM embedding as `wavlm_embedding`.")
        if x.ndim == 1:
            x = x.unsqueeze(0)
        elif x.ndim == 3 and x.shape[-1] == self.config.in_dim:
            # Mean-pool an optional [batch, time, 768] representation.
            x = x.mean(dim=1)
        return self.net(x).squeeze(-1)


AutoConfig.register("chucklenet", ChuckleNetConfig)
AutoModelForAudioClassification.register(ChuckleNetConfig, ChuckleNetDetector)
