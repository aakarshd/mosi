"""Learning center integration — course modules and contextual linking.

Provides course metadata and contextual links from analysis screens
to relevant learning content. Actual course content is managed by
the content team via external CMS; this module provides the integration
hooks and registration.
"""

from dataclasses import dataclass


@dataclass
class CourseModule:
    id: str
    title: str
    description: str
    category: str
    url_path: str
    related_screens: list[str]  # Screen IDs where contextual links appear


# Registered course modules
COURSE_MODULES = [
    CourseModule(
        id="mosi-3-layer",
        title="MOSI 3-Layer Approach",
        description="Understanding the Margin of Safety framework: how Layer 1 screening, Layer 2 AI analysis, and Layer 3 technical rules work together.",
        category="fundamentals",
        url_path="/learn/mosi-3-layer",
        related_screens=["screener_dashboard", "stock_detail_summary"],
    ),
    CourseModule(
        id="screeners-explained",
        title="Screeners Explained",
        description="Deep dive into Passive Income, Growth, and PE Expansion screener models and their criteria.",
        category="fundamentals",
        url_path="/learn/screeners",
        related_screens=["screener_dashboard", "stock_detail_layer1"],
    ),
    CourseModule(
        id="reading-ai-analysis",
        title="Reading AI Analysis",
        description="How to interpret the 11-point AI analysis, Multi-Bagger Score, and verdict. What each analysis point means for your investment thesis.",
        category="analysis",
        url_path="/learn/ai-analysis",
        related_screens=["stock_detail_layer2"],
    ),
    CourseModule(
        id="technical-rules",
        title="Setting Technical Rules",
        description="Entry, exit, and addition rules explained. When to use breakout vs MACD consolidation, stop-loss strategies, and position sizing.",
        category="trading",
        url_path="/learn/technical-rules",
        related_screens=["stock_detail_layer3", "settings_trading_rules"],
    ),
    CourseModule(
        id="behavioral-discipline",
        title="Behavioral Discipline",
        description="Common behavioral patterns that hurt returns: FOMO, early selling, averaging down. How MOSI helps build disciplined habits.",
        category="psychology",
        url_path="/learn/behavioral",
        related_screens=["journal_view", "behavioral_report"],
    ),
]


def get_all_courses() -> list[CourseModule]:
    return COURSE_MODULES


def get_courses_for_screen(screen_id: str) -> list[CourseModule]:
    """Get contextual course links for a specific screen."""
    return [c for c in COURSE_MODULES if screen_id in c.related_screens]


def get_course_by_id(course_id: str) -> CourseModule | None:
    for c in COURSE_MODULES:
        if c.id == course_id:
            return c
    return None
