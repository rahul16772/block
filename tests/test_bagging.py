from typing import Sequence

import torch
import torch.nn as nn

from blockassist.merging.bagging import bag_models


class TestBagging:
    def test_bagging_simple(self):
        models = [nn.Identity(10, 5) for _ in range(2)]
        bagged_model = bag_models(models, weights=[0.2, 0.2])

        x = torch.ones(2, 10)
        assert torch.allclose(bagged_model(x), torch.ones(2, 10) * 0.4)

        # Example with custom aggregation function
        def max_confidence_aggregation(outputs: Sequence[torch.Tensor]) -> torch.Tensor:
            max_values = [torch.max(output).item() for output in outputs]
            max_idx = max_values.index(max(max_values))
            return outputs[max_idx]

        bagged_max_model = bag_models(models, aggregation_fn=max_confidence_aggregation)
        assert torch.allclose(
            bagged_max_model(x), models[0](x)
        )  # All models are identical, so any one will do
