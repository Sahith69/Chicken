"""Loss functions for Poultry Disease Detection (Weighted Cross-Entropy and Focal Loss)."""

from typing import Dict, List, Optional, Union
import torch
import torch.nn as nn
import torch.nn.functional as F


class WeightedCrossEntropyLoss(nn.Module):
    """Class-weighted Cross-Entropy Loss."""

    def __init__(self, weight: Optional[torch.Tensor] = None, reduction: str = "mean"):
        super().__init__()
        self.register_buffer("weight", weight)
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        return F.cross_entropy(logits, targets, weight=self.weight, reduction=self.reduction)


class FocalLoss(nn.Module):
    """Multi-class Focal Loss with class weighting and focusing parameter gamma.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    """

    def __init__(
        self,
        gamma: float = 2.0,
        weight: Optional[torch.Tensor] = None,
        reduction: str = "mean",
    ):
        super().__init__()
        self.gamma = gamma
        self.register_buffer("weight", weight)
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Numerically stable log_softmax
        log_prob = F.log_softmax(logits, dim=-1)
        prob = torch.exp(log_prob)

        # Gather probability of true target class
        target_prob = prob.gather(1, targets.unsqueeze(1)).squeeze(1)
        target_log_prob = log_prob.gather(1, targets.unsqueeze(1)).squeeze(1)

        # Modulating factor (1 - p_t)^gamma
        focal_weight = torch.pow(1.0 - target_prob, self.gamma)

        # Apply class weights if provided
        if self.weight is not None:
            class_weight = self.weight.gather(0, targets)
            focal_weight = focal_weight * class_weight

        loss = -focal_weight * target_log_prob

        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        return loss


def compute_class_weights(
    class_counts: Union[List[int], Dict[str, int]],
    device: Optional[torch.device] = None,
) -> torch.Tensor:
    """Compute balanced inverse frequency class weights: w_c = N / (K * N_c)."""
    if isinstance(class_counts, dict):
        counts = list(class_counts.values())
    else:
        counts = class_counts

    total_samples = sum(counts)
    num_classes = len(counts)
    weights = [total_samples / (num_classes * c) for c in counts]
    # Normalize weights so sum equals num_classes
    weights = [w / sum(weights) * num_classes for w in weights]
    tensor_weights = torch.tensor(weights, dtype=torch.float32)
    if device is not None:
        tensor_weights = tensor_weights.to(device)
    return tensor_weights


def get_loss_fn(
    config: Dict,
    class_counts: Optional[Union[List[int], Dict[str, int]]] = None,
    device: Optional[torch.device] = None,
) -> nn.Module:
    """Factory function returning the configured loss criterion."""
    loss_cfg = config.get("loss", {})
    loss_type = loss_cfg.get("type", "weighted_ce")
    gamma = float(loss_cfg.get("gamma", 2.0))

    weights = None
    if class_counts is not None:
        weights = compute_class_weights(class_counts, device=device)

    if loss_type == "focal":
        criterion = FocalLoss(gamma=gamma, weight=weights)
    elif loss_type in ("weighted_ce", "cross_entropy"):
        criterion = WeightedCrossEntropyLoss(weight=weights)
    else:
        raise ValueError(f"Unknown loss type: {loss_type}. Choose 'weighted_ce' or 'focal'.")

    return criterion


if __name__ == "__main__":
    dummy_counts = [1734, 1683, 394, 1838]
    w = compute_class_weights(dummy_counts)
    print("Class counts:", dummy_counts)
    print("Computed balanced class weights:", [round(float(x), 4) for x in w])

    logits = torch.randn(4, 4)
    targets = torch.tensor([0, 1, 2, 3])

    ce_fn = WeightedCrossEntropyLoss(weight=w)
    fl_fn = FocalLoss(gamma=2.0, weight=w)

    print("CE loss test:", float(ce_fn(logits, targets)))
    print("Focal loss test:", float(fl_fn(logits, targets)))
