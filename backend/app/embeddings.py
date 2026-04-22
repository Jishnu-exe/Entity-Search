from functools import lru_cache
from typing import List

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import models
from torchvision.models import EfficientNet_B0_Weights


class EmbeddingModel:
    def __init__(self) -> None:
        weights = EfficientNet_B0_Weights.DEFAULT
        base = models.efficientnet_b0(weights=weights)
        self.model = torch.nn.Sequential(
            base.features,
            base.avgpool,
            torch.nn.Flatten(),
        )
        self.model.eval()
        self.model.to("cpu")
        self.transform = weights.transforms()

    @torch.inference_mode()
    def embed_image(self, image: Image.Image) -> List[float]:
        tensor = self.transform(image).unsqueeze(0)
        vector = self.model(tensor)
        vector = F.normalize(vector, p=2, dim=1)
        return vector.cpu().numpy()[0].astype(float).tolist()


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
