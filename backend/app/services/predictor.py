import pickle
from pathlib import Path
from typing import Any

import numpy as np
from joblib import load

from app.core.config import get_settings
from app.schemas import BuyboxFeatureInput

FEATURE_ORDER = [
    "SellPrice",
    "ShippingPrice",
    "TotalPrice",
    "MinCompetitorPrice",
    "MinTotalPriceInSnapshot",
    "PriceGap",
    "TotalPriceGap",
    "PriceGapPercent",
    "PriceRank",
    "PriceRankNormalized",
    "TotalCompetitorsInSnapshot",
    "PositiveFeedbackPercent",
    "MaxFeedbackInSnapshot",
    "FeedbackGapFromMax",
    "IsMinSellPrice",
    "IsMinTotalPrice",
    "IsFBA",
]


class BuyboxPredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = "fallback-heuristic"
        self.model: Any | None = None
        self._try_load_model()

    def _try_load_model(self) -> None:
        path = Path(self.settings.buybox_model_path)
        if not path.exists():
            return
        try:
            # joblib works for most sklearn dumps; stdlib pickle as fallback for .pkl
            if path.suffix.lower() in {".pkl", ".pickle"}:
                with path.open("rb") as f:
                    self.model = pickle.load(f)
            else:
                self.model = load(path)
            self.model_name = "trained-model"
        except Exception:
            self.model = None
            self.model_name = "fallback-heuristic"

    def _to_vector(self, features: BuyboxFeatureInput) -> np.ndarray:
        raw = features.model_dump()
        values = [float(raw[name]) for name in FEATURE_ORDER]
        return np.array([values], dtype=float)

    def predict(self, features: BuyboxFeatureInput) -> tuple[float, float, str]:
        # Fallback keeps project demo functional when model file is absent.
        if self.model is None:
            recommended = max(
                0.0,
                features.MinCompetitorPrice
                - 0.01
                + (0.05 if features.IsFBA >= 1 else 0)
                + (features.PositiveFeedbackPercent - 90) * 0.002,
            )
            return round(recommended, 2), 0.62, self.model_name

        X = self._to_vector(features)
        pred = self.model.predict(X)
        recommended = float(pred[0]) if hasattr(pred, "__len__") else float(pred)
        confidence = 0.82
        return round(recommended, 2), confidence, self.model_name


predictor = BuyboxPredictor()
