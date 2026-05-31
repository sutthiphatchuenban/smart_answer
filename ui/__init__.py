"""UI components package for Smart Answer."""

from .navigation import NavigationFrame
from .dashboard_page import DashboardPage
from .history_page import HistoryPage
from .settings_page import SettingsPage
from .coaching_card import create_coaching_card

__all__ = [
    "NavigationFrame",
    "DashboardPage",
    "HistoryPage",
    "SettingsPage",
    "create_coaching_card",
]

