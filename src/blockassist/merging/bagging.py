from typing import Callable, List, Sequence

import torch
import torch.nn as nn


def bag_models(
    models: Sequence[nn.Module],
    aggregation_fn: Callable | None = None,
    weights: Sequence[float] | None = None,
) -> Callable:
    """
    Creates a function that aggregates (bags) the outputs of multiple PyTorch models.

    Args:
        models: List of nn.Module instances to ensemble
        aggregation_fn: Optional custom aggregation function. If None, uses weighted mean
        weights: Optional weights for each model. If None, equal weights are used

    Returns:
        A callable that takes the same inputs as the models and returns aggregated outputs
    """
    if not models:
        raise ValueError("At least one model must be provided")

    if weights is None:
        weights = [1.0 / len(models)] * len(models)
    elif len(weights) != len(models):
        raise ValueError(
            f"Number of weights ({len(weights)}) must match number of models ({len(models)})"
        )

    weights_tensor = torch.tensor(weights)

    # Default aggregation is weighted average
    if aggregation_fn is None:

        def default_aggregation(outputs: List[torch.Tensor]) -> torch.Tensor:
            stacked = torch.stack(outputs, dim=-1)
            weighted = stacked * weights_tensor.view(-1, *[1] * (stacked.dim() - 1)).to(
                stacked.device
            )
            return weighted.sum(dim=-1)

        aggregation_fn = default_aggregation

    def bagged_forward(*args, **kwargs):
        outputs = []
        with torch.no_grad():
            for model in models:
                model.eval()
                outputs.append(model(*args, **kwargs))

        return aggregation_fn(outputs)

    return bagged_forward
