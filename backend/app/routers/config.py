from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from app.schemas.config import (
    ModelSelectionRequest, ModelSelectionResponse,
    TradingRulesRequest, TradingRulesResponse,
    AlertPreferencesRequest, AlertPreferencesResponse,
)

router = APIRouter(tags=["config"])


@router.get("/models", response_model=ModelSelectionResponse)
async def get_model_selections(user: dict = Depends(get_current_user)):
    """Get user's selected screener models."""
    # TODO: Wire to database
    return ModelSelectionResponse(models=[])


@router.put("/models", response_model=ModelSelectionResponse)
async def update_model_selections(request: ModelSelectionRequest, user: dict = Depends(get_current_user)):
    """Update user's screener model selections."""
    # TODO: Wire to database
    raise NotImplementedError


@router.get("/trading-rules", response_model=TradingRulesResponse)
async def get_trading_rules(user: dict = Depends(get_current_user)):
    """Get user's trading rule configuration."""
    # TODO: Wire to database
    raise NotImplementedError


@router.put("/trading-rules", response_model=TradingRulesResponse)
async def update_trading_rules(request: TradingRulesRequest, user: dict = Depends(get_current_user)):
    """Update user's trading rules."""
    # TODO: Wire to database
    raise NotImplementedError


@router.get("/alerts", response_model=AlertPreferencesResponse)
async def get_alert_preferences(user: dict = Depends(get_current_user)):
    """Get user's alert preferences."""
    # TODO: Wire to database
    raise NotImplementedError


@router.put("/alerts", response_model=AlertPreferencesResponse)
async def update_alert_preferences(request: AlertPreferencesRequest, user: dict = Depends(get_current_user)):
    """Update user's alert preferences."""
    # TODO: Wire to database
    raise NotImplementedError
