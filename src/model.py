"""Model architectures for Poultry Disease Detection."""

from typing import Dict, Optional, Union
import torch
import torch.nn as nn


class BaselineCNN(nn.Module):
    """A small convolutional neural network built from scratch (4 conv blocks).

    Architecture:
      Conv(3->16) -> BN -> ReLU -> MaxPool
      Conv(16->32) -> BN -> ReLU -> MaxPool
      Conv(32->64) -> BN -> ReLU -> MaxPool
      Conv(64->128) -> BN -> ReLU -> AdaptiveAvgPool2d((1, 1))
      Flatten -> Dropout(0.3) -> Linear(128, num_classes)
    """

    def __init__(self, num_classes: int = 4, in_channels: int = 3, dropout_rate: float = 0.3):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(in_channels, 16, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 224 -> 112
            # Block 2
            nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 112 -> 56
            # Block 3
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # 56 -> 28
            # Block 4
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),  # 28 -> 1
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=dropout_rate),
            nn.Linear(128, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        logits = self.classifier(feat)
        return logits


def build_model(
    config_or_name: Union[str, Dict] = "scratch_cnn",
    num_classes: int = 4,
    pretrained: bool = False,
) -> nn.Module:
    """Factory function to build baseline scratch CNN or transfer learning backbones."""
    if isinstance(config_or_name, dict):
        backbone_name = config_or_name.get("backbone", "scratch_cnn")
        classes = config_or_name.get("classes", [])
        num_classes = len(classes) if classes else num_classes
    else:
        backbone_name = config_or_name

    if backbone_name in ("scratch_cnn", "baseline_cnn"):
        model = BaselineCNN(num_classes=num_classes)
    else:
        import timm
        model = timm.create_model(backbone_name, pretrained=pretrained, num_classes=num_classes)

    return model


if __name__ == "__main__":
    net = BaselineCNN(num_classes=4)
    dummy_input = torch.randn(2, 3, 224, 224)
    out = net(dummy_input)
    print("BaselineCNN initialized successfully.")
    print("Output shape:", out.shape)
    num_params = sum(p.numel() for p in net.parameters() if p.requires_grad)
    print(f"Total trainable parameters: {num_params:,}")
