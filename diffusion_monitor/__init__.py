"""
Diffusion Model Monitoring Platform

Production-grade monitoring and visualization for diffusion-based language models.
"""

from .quality_detector import QualityDetector, QualitySignal, QualityBaseline
from .alert_manager import (
    AlertManager,
    AlertSeverity,
    Alert,
    AlertChannel,
    SlackChannel,
    PagerDutyChannel,
    WebhookChannel,
    ConsoleChannel,
)

__version__ = "0.1.0"
__author__ = "Brian Worthington"
__all__ = [
    "QualityDetector",
    "QualitySignal",
    "QualityBaseline",
    "AlertManager",
    "AlertSeverity",
    "Alert",
    "AlertChannel",
    "SlackChannel",
    "PagerDutyChannel",
    "WebhookChannel",
    "ConsoleChannel",
]
