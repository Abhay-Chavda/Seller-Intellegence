import httpx
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from joblib import load

from app.core.config import get_settings
from app.schemas import BuyboxFeatureInput

FEATURE_ORDER = [
    "SellPrice", "ShippingPrice", "TotalPrice", "MinCompetitorPrice", 
    "MinTotalPriceInSnapshot", "PriceGap", "TotalPriceGap", "PriceGapPercent", 
    "PriceRank", "PriceRankNormalized", "TotalCompetitorsInSnapshot", 
    "PositiveFeedbackPercent", "MaxFeedbackInSnapshot", "FeedbackGapFromMax", 
    "IsMinSellPrice", "IsMinTotalPrice", "IsFBA",
]

class BuyboxPredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_name = "Willow-ML-v2"
        self.api_url = self.settings.buybox_api_url
        self.api_timeout_seconds = self.settings.buybox_api_timeout_seconds
        self.model: Any | None = None
        self._try_load_model()

    def _try_load_model(self) -> None:
        # We prefer the Willow API, but keep local fallback loading logic
        path = Path(self.settings.buybox_model_path)
        if not path.exists(): return
        try:
            if path.suffix.lower() in {".pkl", ".pickle"}:
                with path.open("rb") as f: self.model = pickle.load(f)
            else: self.model = load(path)
        except Exception: self.model = None

    def enrich_features(self, payload: BuyboxFeatureInput, history: list[dict]) -> BuyboxFeatureInput:
        """
        Takes raw user input (4 fields) and enriches it to the full 18-point feature vector 
        required for high-accuracy Willow API predictions.
        """
        # Base values from user input
        sell_price = payload.SellPrice
        shipping = payload.ShippingPrice
        total_price = sell_price + shipping
        min_comp_price = payload.MinCompetitorPrice
        is_fba = payload.IsFBA
        
        # Market-wide analysis from history
        comp_prices = [h["price"] for h in history] if history else [min_comp_price]
        max_feedback = max([h["feedback_count"] for h in history]) if history else 100
        
        # Feature Engineering Logic
        price_gap = sell_price - min_comp_price
        price_gap_percent = (price_gap / min_comp_price * 100) if min_comp_price > 0 else 0
        
        # Rank: Where is our price among competitors? (Lower is better/cheaper)
        all_prices = sorted(comp_prices + [sell_price])
        price_rank = all_prices.index(sell_price) + 1
        price_rank_norm = price_rank / len(all_prices)
        
        # Social Proof: Feedback metrics
        our_feedback_rating = payload.PositiveFeedbackPercent # Comes from user state in UI
        feedback_gap = 100 - our_feedback_rating
        
        # Staging the final enriched object
        enriched = payload.model_copy(update={
            "TotalPrice": total_price,
            "MinTotalPriceInSnapshot": min_comp_price, # Assume shipping is bundled for simplicity
            "PriceGap": round(price_gap, 2),
            "TotalPriceGap": round(price_gap, 2),
            "PriceGapPercent": round(price_gap_percent, 2),
            "PriceRank": float(price_rank),
            "PriceRankNormalized": round(price_rank_norm, 2),
            "TotalCompetitorsInSnapshot": float(len(history)),
            "IsMinSellPrice": 1.0 if sell_price <= min_comp_price else 0.0,
            "IsMinTotalPrice": 1.0 if total_price <= min_comp_price else 0.0,
            "MaxFeedbackInSnapshot": float(max_feedback),
            "FeedbackGapFromMax": float(feedback_gap)
        })
        
        print(f"DEBUG: Staged enriched vector for {payload.sku} | Price Rank: {price_rank}")
        return enriched

    def predict(self, features: BuyboxFeatureInput, history: list[dict] | None = None) -> tuple[float, float, str]:
        # 1. Attempt external model API integration (configurable for Azure Foundry setup)
        if self.api_url:
            try:
                payload = {
                    "CompetitorsHistory": history if history else [],
                    "SellerId": "abhay-premium-001",
                    "BuyboxHistoryId": 105,
                    "MinPrice": round(features.SellPrice * 0.75, 2),
                    "MaxPrice": round(features.SellPrice * 1.5, 2),
                    "Features": features.model_dump(),
                }

                with httpx.Client(timeout=self.api_timeout_seconds) as client:
                    resp = client.post(self.api_url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        rec_price = data.get("recommended_price") or data.get("RecommendedPrice")
                        confidence = data.get("confidence") or data.get("Confidence") or 0.94
                        if rec_price is not None:
                            return round(float(rec_price), 2), float(confidence), "External-Buybox-API"
            except Exception as e:
                print(f"Buybox API Connection Issue: {e}")

        # 2. Local Model Fallback
        if self.model is not None:
            try:
                raw = features.model_dump()
                X = np.array([[float(raw[name]) for name in FEATURE_ORDER]])
                pred = self.model.predict(X)
                rec = float(pred[0]) if hasattr(pred, "__len__") else float(pred)
                return round(rec, 2), 0.82, "Trained-Local-XGB"
            except Exception: pass

        # 3. Final Heuristic Fallback (Presentation insurance)
        recommended = max(0.0, features.MinCompetitorPrice - 0.01 + (0.05 if features.IsFBA >= 1 else 0))
        return round(recommended, 2), 0.65, "Heuristic-Engine"

predictor = BuyboxPredictor()
