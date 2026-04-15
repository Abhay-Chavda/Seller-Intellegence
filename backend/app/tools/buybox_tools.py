from typing import Any

from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.services.predictor import predictor

from .base import ToolSpec, json_schema


def _predict_buybox(
    db: Session,
    user: models.User,
    args: schemas.PredictBuyboxToolArgs,
) -> dict[str, Any]:
    features = args.to_feature_input()
    history_records = (
        db.query(models.CompetitorPriceRecord)
        .join(models.Product)
        .filter(models.Product.sku == features.sku, models.Product.seller_id == user.id)
        .all()
    )
    history = [
        {
            "price": row.price,
            "is_fba": row.is_fba,
            "feedback_count": row.feedback_count,
            "feedback_rating": row.feedback_rating,
        }
        for row in history_records
    ]

    enriched = predictor.enrich_features(features, history=history)
    recommended_price, confidence, model_name = predictor.predict(enriched, history=history)
    crud.create_buybox_prediction(
        db=db,
        seller_id=user.id,
        features=enriched,
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    )

    return schemas.BuyboxPredictionOut(
        recommended_price=recommended_price,
        confidence=confidence,
        model_name=model_name,
    ).model_dump(mode="json")


BUYBOX_TOOL_SPECS: dict[str, ToolSpec] = {
    "predict_buybox": ToolSpec(
        name="predict_buybox",
        description="Predict recommended buybox price using configured model API/local fallback.",
        args_model=schemas.PredictBuyboxToolArgs,
        output_schema=json_schema(schemas.BuyboxPredictionOut),
        handler=_predict_buybox,
    )
}
