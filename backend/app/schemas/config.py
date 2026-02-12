from pydantic import BaseModel


class ModelSelectionItem(BaseModel):
    model_type: str  # passive_income/growth/pe_expansion
    is_active: bool


class ModelSelectionResponse(BaseModel):
    models: list[ModelSelectionItem]


class ModelSelectionRequest(BaseModel):
    models: list[ModelSelectionItem]


class TradingRulesResponse(BaseModel):
    entry_rule: str
    addition_cap: str
    exit_rule: str
    signal_source: str


class TradingRulesRequest(BaseModel):
    entry_rule: str
    addition_cap: str
    exit_rule: str
    signal_source: str


class AlertPreferencesResponse(BaseModel):
    channel_push: bool
    channel_email: bool
    channel_sms: bool
    smart_alerts: bool
    frequency: str


class AlertPreferencesRequest(BaseModel):
    channel_push: bool
    channel_email: bool
    channel_sms: bool
    smart_alerts: bool
    frequency: str
