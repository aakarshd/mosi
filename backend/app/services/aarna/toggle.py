"""Signal source toggle — switches between Layer 3 and Aarna.

When the user toggles their signal source preference, this module:
1. Updates user_config in the database
2. Triggers readiness recomputation for all the user's tracked stocks
"""

import logging

from sqlalchemy.orm import Session

from app.models.user_config import UserTradingRules, SignalSource

logger = logging.getLogger(__name__)


def get_active_signal_source(db: Session, user_id: str) -> str:
    """Get the user's active signal source name."""
    rules = db.query(UserTradingRules).filter(UserTradingRules.user_id == user_id).first()
    if rules is None:
        return SignalSource.LAYER3.value
    return rules.signal_source.value


def switch_signal_source(db: Session, user_id: str, new_source: str) -> str:
    """Switch the user's signal source and persist to DB.

    Returns the new signal source name.
    """
    source_enum = SignalSource(new_source)

    rules = db.query(UserTradingRules).filter(UserTradingRules.user_id == user_id).first()
    if rules is None:
        rules = UserTradingRules(user_id=user_id, signal_source=source_enum)
        db.add(rules)
    else:
        rules.signal_source = source_enum

    db.commit()
    logger.info(f"User {user_id} switched signal source to {new_source}")
    return source_enum.value
