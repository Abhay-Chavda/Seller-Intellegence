from sqlalchemy.orm import Session

from app import crud, schemas
from app.models import User
from app.services.predictor import predictor


def run_agent_task(db: Session, user: User, payload: schemas.AgentChatRequest) -> schemas.AgentChatResponse:
    prompt = payload.prompt.strip()
    lowered = prompt.lower()

    if "total sales" in lowered or "sales summary" in lowered:
        summary = crud.get_dashboard_summary(db, user.id)
        result = (
            f"Total sales: {summary['total_sales']}, "
            f"Total orders: {summary['total_orders']}, "
            f"Units sold: {summary['total_units_sold']}"
        )
        action = "get_sales_summary"
        crud.create_agent_task(db, user.id, prompt, action, result)
        return schemas.AgentChatResponse(action=action, result=result)

    if "predict buybox" in lowered:
        products = crud.list_products(db, user.id)
        if not products:
            result = "No products found to run prediction on."
            action = "predict_buybox"
            crud.create_agent_task(db, user.id, prompt, action, result)
            return schemas.AgentChatResponse(action=action, result=result)

        product = products[0]
        features = schemas.BuyboxFeatureInput(
            sku=product.sku,
            SellPrice=product.sell_price,
            ShippingPrice=0.0,
            TotalPrice=product.sell_price,
            MinCompetitorPrice=max(0.0, product.sell_price - 1.0),
            MinTotalPriceInSnapshot=max(0.0, product.sell_price - 1.0),
            PriceGap=1.0,
            TotalPriceGap=1.0,
            PriceGapPercent=2.0,
            PriceRank=2.0,
            PriceRankNormalized=0.2,
            TotalCompetitorsInSnapshot=10.0,
            PositiveFeedbackPercent=95.0,
            MaxFeedbackInSnapshot=99.0,
            FeedbackGapFromMax=4.0,
            IsMinSellPrice=0.0,
            IsMinTotalPrice=0.0,
            IsFBA=1.0,
        )
        rec_price, confidence, model_name = predictor.predict(features)
        crud.create_buybox_prediction(db, user.id, features, rec_price, confidence, model_name)
        result = f"Suggested buybox price for {product.sku}: {rec_price} ({model_name})"
        action = "predict_buybox"
        crud.create_agent_task(db, user.id, prompt, action, result)
        return schemas.AgentChatResponse(action=action, result=result)

    result = (
        "I can currently do: sales summary and buybox prediction. "
        "Try: 'show total sales' or 'predict buybox'."
    )
    action = "unknown"
    crud.create_agent_task(db, user.id, prompt, action, result)
    return schemas.AgentChatResponse(action=action, result=result)
