"""Multimodal Poultry Network Architecture.

Fuses EfficientNet-B0 vision embeddings (1280-d) with Clinical Metadata embeddings (64-d)
via a Gated Feature Fusion Attention mechanism.
"""

import torch
import torch.nn as nn
import timm


class MultimodalPoultryNet(nn.Module):
    """Dual-Stream Vision + Clinical Metadata Neural Network with Gated Feature Fusion."""

    def __init__(self, num_classes: int = 4, meta_dim: int = 5, embed_dim: int = 64):
        super().__init__()
        # 1. Vision Backbone (EfficientNet-B0)
        self.vision_backbone = timm.create_model("efficientnet_b0", pretrained=True, num_classes=0)
        num_vision_feats = self.vision_backbone.num_features  # 1280

        # 2. Metadata Processing Branch
        self.meta_branch = nn.Sequential(
            nn.Linear(meta_dim, 32),
            nn.BatchNorm1d(32),
            nn.SiLU(),
            nn.Linear(32, embed_dim),
            nn.BatchNorm1d(embed_dim),
            nn.SiLU(),
        )

        # 3. Gated Attention Fusion Layer
        self.gate = nn.Sequential(
            nn.Linear(num_vision_feats + embed_dim, 1),
            nn.Sigmoid(),
        )

        # 4. Multimodal Classification Head
        fusion_dim = num_vision_feats + embed_dim
        self.classifier = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, image: torch.Tensor, metadata: torch.Tensor):
        # Extract features
        v = self.vision_backbone(image)  # [batch, 1280]
        m = self.meta_branch(metadata)   # [batch, 64]

        # Compute gating weight
        combined = torch.cat([v, m], dim=1)  # [batch, 1344]
        g = self.gate(combined)               # [batch, 1]

        # Gated fusion
        fused = torch.cat([v, g * m], dim=1)  # [batch, 1344]

        # Compute classification logits
        logits = self.classifier(fused)
        return logits, g
