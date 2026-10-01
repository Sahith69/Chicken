"""Multimodal Poultry Network Architectures.

Includes:
1. MultimodalPoultryNet: Dual-Stream (Stool Image + Clinical Metadata)
2. TripleStreamPoultryNet: Triple-Stream (Stool Image + Bird Image + Clinical Metadata with Cross-Attention)
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


class TripleStreamPoultryNet(nn.Module):
    """Triple-Stream Multimodal Network: Stool Photo + Bird Photo + Clinical Metadata with Cross-Attention."""

    def __init__(self, num_classes: int = 4, meta_dim: int = 5, embed_dim: int = 64):
        super().__init__()
        # 1. Dual Vision Encoders (EfficientNet-B0)
        self.stool_encoder = timm.create_model("efficientnet_b0", pretrained=True, num_classes=0)
        self.bird_encoder = timm.create_model("efficientnet_b0", pretrained=True, num_classes=0)
        num_vision_feats = 1280

        # 2. Metadata Branch
        self.meta_branch = nn.Sequential(
            nn.Linear(meta_dim, 32),
            nn.BatchNorm1d(32),
            nn.SiLU(),
            nn.Linear(32, embed_dim),
            nn.BatchNorm1d(embed_dim),
            nn.SiLU(),
        )

        # 3. Cross-Attention Vision Fusion
        self.query_proj = nn.Linear(num_vision_feats, 256)
        self.key_proj = nn.Linear(num_vision_feats, 256)
        self.value_proj = nn.Linear(num_vision_feats, num_vision_feats)

        # 4. Gated Attention Fusion Layer
        self.gate = nn.Sequential(
            nn.Linear(num_vision_feats + embed_dim, 1),
            nn.Sigmoid(),
        )

        # 5. Classifier Head
        fusion_dim = num_vision_feats + embed_dim
        self.classifier = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, stool_image: torch.Tensor, bird_image: torch.Tensor, metadata: torch.Tensor):
        # Feature Extraction
        v_stool = self.stool_encoder(stool_image)  # [batch, 1280]
        v_bird = self.bird_encoder(bird_image)     # [batch, 1280]
        m_meta = self.meta_branch(metadata)         # [batch, 64]

        # Stage 1: Cross-Attention Vision Fusion (Stool queries Bird)
        q = self.query_proj(v_stool)
        k = self.key_proj(v_bird)
        v = self.value_proj(v_bird)
        
        scores = torch.matmul(q, k.transpose(-2, -1)) / 16.0  # sqrt(256) = 16
        attn_weights = torch.softmax(scores, dim=-1)
        v_attn = torch.matmul(attn_weights, v)
        v_unified = v_stool + v_attn

        # Stage 2: Gated Metadata Integration
        combined = torch.cat([v_unified, m_meta], dim=1)
        g = self.gate(combined)
        fused = torch.cat([v_unified, g * m_meta], dim=1)

        # Classification Logits
        logits = self.classifier(fused)
        return logits, g
