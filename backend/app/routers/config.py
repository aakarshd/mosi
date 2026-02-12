from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.screener import ModelType
from app.models.user_config import (
    UserModelSelection, UserTradingRules, UserAlertPreferences,
    EntryRule, AdditionCap, ExitRule, SignalSource,
)
from app.schemas.config import (
    ModelSelectionRequest, ModelSelectionResponse, ModelSelectionItem,
    TradingRulesRequest, TradingRulesResponse,
    AlertPreferencesRequest, AlertPreferencesResponse,
)

router = APIRouter(tags=["config"])


@router.get("/models", response_model=ModelSelectionResponse)
async def get_model_selections(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's selected screener models."""
    user_id = user.get("sub", "")
    selections = db.query(UserModelSelection).filter(UserModelSelection.user_id == user_id).all()

    if not selections:
        # Default: all models active
        return ModelSelectionResponse(models=[
            ModelSelectionItem(model_type=mt.value, is_active=True)
            for mt in ModelType
        ])

    return ModelSelectionResponse(models=[
        ModelSelectionItem(model_type=s.model_type.value, is_active=s.is_active)
        for s in selections
    ])


@router.put("/models", response_model=ModelSelectionResponse)
async def update_model_selections(
    request: ModelSelectionRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's screener model selections."""
    user_id = user.get("sub", "")

    # Delete existing and replace
    db.query(UserModelSelection).filter(UserModelSelection.user_id == user_id).delete()

    for item in request.models:
        selection = UserModelSelection(
            user_id=user_id,
            model_type=ModelType(item.model_type),
            is_active=item.is_active,
        )
        db.add(selection)

    db.commit()

    return ModelSelectionResponse(models=request.models)


@router.get("/trading-rules", response_model=TradingRulesResponse)
async def get_trading_rules(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's trading rule configuration."""
    user_id = user.get("sub", "")
    rules = db.query(UserTradingRules).filter(UserTradingRules.user_id == user_id).first()

    if rules is None:
        # Return defaults
        return TradingRulesResponse(
            entry_rule=EntryRule.BREAKOUT_VOLUME_MACD.value,
            addition_cap=AdditionCap.MAX_5_PCT.value,
            exit_rule=ExitRule.EIGHT_PCT_DROP.value,
            signal_source=SignalSource.LAYER3.value,
        )

    return TradingRulesResponse(
        entry_rule=rules.entry_rule.value,
        addition_cap=rules.addition_cap.value,
        exit_rule=rules.exit_rule.value,
        signal_source=rules.signal_source.value,
    )


@router.put("/trading-rules", response_model=TradingRulesResponse)
async def update_trading_rules(
    request: TradingRulesRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's trading rules."""
    user_id = user.get("sub", "")
    rules = db.query(UserTradingRules).filter(UserTradingRules.user_id == user_id).first()

    if rules is None:
        rules = UserTradingRules(user_id=user_id)
        db.add(rules)

    rules.entry_rule = EntryRule(request.entry_rule)
    rules.addition_cap = AdditionCap(request.addition_cap)
    rules.exit_rule = ExitRule(request.exit_rule)
    rules.signal_source = SignalSource(request.signal_source)

    db.commit()

    return TradingRulesResponse(
        entry_rule=rules.entry_rule.value,
        addition_cap=rules.addition_cap.value,
        exit_rule=rules.exit_rule.value,
        signal_source=rules.signal_source.value,
    )


@router.get("/alerts", response_model=AlertPreferencesResponse)
async def get_alert_preferences(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's alert preferences."""
    user_id = user.get("sub", "")
    prefs = db.query(UserAlertPreferences).filter(UserAlertPreferences.user_id == user_id).first()

    if prefs is None:
        return AlertPreferencesResponse(
            channel_push=True, channel_email=False, channel_sms=False,
            smart_alerts=True, frequency="immediate",
        )

    return AlertPreferencesResponse(
        channel_push=prefs.channel_push,
        channel_email=prefs.channel_email,
        channel_sms=prefs.channel_sms,
        smart_alerts=prefs.smart_alerts,
        frequency=prefs.frequency,
    )


@router.put("/alerts", response_model=AlertPreferencesResponse)
async def update_alert_preferences(
    request: AlertPreferencesRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's alert preferences."""
    user_id = user.get("sub", "")
    prefs = db.query(UserAlertPreferences).filter(UserAlertPreferences.user_id == user_id).first()

    if prefs is None:
        prefs = UserAlertPreferences(user_id=user_id)
        db.add(prefs)

    prefs.channel_push = request.channel_push
    prefs.channel_email = request.channel_email
    prefs.channel_sms = request.channel_sms
    prefs.smart_alerts = request.smart_alerts
    prefs.frequency = request.frequency

    db.commit()

    return AlertPreferencesResponse(
        channel_push=prefs.channel_push,
        channel_email=prefs.channel_email,
        channel_sms=prefs.channel_sms,
        smart_alerts=prefs.smart_alerts,
        frequency=prefs.frequency,
    )
