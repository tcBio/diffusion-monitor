"""
Alert Manager for Quality Degradation

Sends alerts to various channels (Slack, PagerDuty, Email, Webhooks).
Manages alert lifecycle (fire, resolve, escalate).
"""

import time
import json
import requests
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert structure"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    timestamp: float

    # Metadata
    model_name: str
    environment: str

    # Alert details
    primary_reason: str
    affected_requests: int
    metrics: Dict

    # Status
    is_resolved: bool = False
    resolved_at: Optional[float] = None


class AlertChannel:
    """Base class for alert channels"""

    def send_alert(self, alert: Alert) -> bool:
        """Send alert (fire or resolve)"""
        raise NotImplementedError

    def test_connection(self) -> bool:
        """Test if channel is reachable"""
        raise NotImplementedError


class SlackChannel(AlertChannel):
    """Send alerts to Slack via webhook"""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel

    def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""

        if not alert.is_resolved:
            color = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900",
                AlertSeverity.CRITICAL: "#ff0000",
            }.get(alert.severity, "#808080")

            title = f"🚨 {alert.title}"
            text = alert.description
        else:
            color = "#36a64f"
            title = f"✅ RESOLVED: {alert.title}"
            duration = alert.resolved_at - alert.timestamp if alert.resolved_at else 0
            text = f"Alert resolved after {duration:.0f} seconds"

        payload = {
            "text": title,
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": text,
                    "fields": [
                        {
                            "title": "Model",
                            "value": alert.model_name,
                            "short": True
                        },
                        {
                            "title": "Environment",
                            "value": alert.environment,
                            "short": True
                        },
                        {
                            "title": "Primary Reason",
                            "value": alert.primary_reason,
                            "short": False
                        },
                        {
                            "title": "Affected Requests",
                            "value": str(alert.affected_requests),
                            "short": True
                        },
                    ],
                    "footer": "Diffusion Monitor",
                    "ts": int(alert.timestamp)
                }
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Slack webhook"""
        test_payload = {
            "text": "🧪 Diffusion Monitor - Test Alert",
            "attachments": [
                {
                    "color": "#36a64f",
                    "text": "This is a test alert. Your Slack integration is working!"
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


class PagerDutyChannel(AlertChannel):
    """Send alerts to PagerDuty"""

    def __init__(self, integration_key: str):
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def send_alert(self, alert: Alert) -> bool:
        """Send alert to PagerDuty"""

        event_action = "resolve" if alert.is_resolved else "trigger"

        payload = {
            "routing_key": self.integration_key,
            "event_action": event_action,
            "dedup_key": alert.alert_id,
            "payload": {
                "summary": alert.title,
                "severity": alert.severity.value,
                "source": alert.model_name,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(alert.timestamp)),
                "custom_details": {
                    "description": alert.description,
                    "primary_reason": alert.primary_reason,
                    "affected_requests": alert.affected_requests,
                    "environment": alert.environment,
                    "metrics": alert.metrics,
                }
            }
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=5
            )
            return response.status_code == 202
        except Exception as e:
            print(f"Failed to send PagerDuty alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test PagerDuty integration"""
        # Send a test trigger and immediately resolve
        test_alert = Alert(
            alert_id="test-connection",
            severity=AlertSeverity.INFO,
            title="Test Connection",
            description="Testing PagerDuty integration",
            timestamp=time.time(),
            model_name="test",
            environment="test",
            primary_reason="test",
            affected_requests=0,
            metrics={},
        )

        # Send and immediately resolve
        sent = self.send_alert(test_alert)
        if sent:
            test_alert.is_resolved = True
            test_alert.resolved_at = time.time()
            self.send_alert(test_alert)

        return sent


class WebhookChannel(AlertChannel):
    """Send alerts to custom webhook"""

    def __init__(self, webhook_url: str, headers: Optional[Dict] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    def send_alert(self, alert: Alert) -> bool:
        """Send alert to webhook"""

        payload = {
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "title": alert.title,
            "description": alert.description,
            "timestamp": alert.timestamp,
            "model_name": alert.model_name,
            "environment": alert.environment,
            "primary_reason": alert.primary_reason,
            "affected_requests": alert.affected_requests,
            "metrics": alert.metrics,
            "is_resolved": alert.is_resolved,
            "resolved_at": alert.resolved_at,
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=5
            )
            return response.status_code in [200, 201, 202]
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test webhook"""
        try:
            response = requests.get(self.webhook_url, timeout=5)
            return response.status_code < 500
        except:
            return False


class ConsoleChannel(AlertChannel):
    """Print alerts to console (for testing/development)"""

    def send_alert(self, alert: Alert) -> bool:
        """Print alert to console"""

        separator = "=" * 80

        if not alert.is_resolved:
            print(f"\n{separator}")
            print(f"🚨 ALERT FIRED: {alert.title}")
            print(separator)
            print(f"Severity: {alert.severity.value.upper()}")
            print(f"Model: {alert.model_name} ({alert.environment})")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}")
            print(f"\nDescription: {alert.description}")
            print(f"\nPrimary Reason: {alert.primary_reason}")
            print(f"Affected Requests: {alert.affected_requests}")
            print(f"\nMetrics:")
            for key, value in alert.metrics.items():
                print(f"  {key}: {value}")
            print(separator)
        else:
            duration = alert.resolved_at - alert.timestamp if alert.resolved_at else 0
            print(f"\n{separator}")
            print(f"✅ ALERT RESOLVED: {alert.title}")
            print(separator)
            print(f"Duration: {duration:.0f} seconds")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.resolved_at))}")
            print(separator)

        return True

    def test_connection(self) -> bool:
        """Console is always available"""
        return True


class AlertManager:
    """
    Manages alert lifecycle and routing

    Features:
    - Multi-channel alerting (Slack, PagerDuty, webhooks)
    - Alert deduplication
    - Auto-resolution tracking
    - Rate limiting (avoid alert storms)
    """

    def __init__(
        self,
        model_name: str = "diffusion-model",
        environment: str = "production",
        rate_limit_seconds: int = 60,
    ):
        self.model_name = model_name
        self.environment = environment
        self.rate_limit_seconds = rate_limit_seconds

        # Channels
        self.channels: List[AlertChannel] = []

        # Active alerts
        self.active_alerts: Dict[str, Alert] = {}

        # Rate limiting
        self.last_alert_time: Dict[str, float] = {}

        # Statistics
        self.alerts_sent = 0
        self.alerts_resolved = 0

    def add_channel(self, channel: AlertChannel) -> bool:
        """Add alert channel"""
        self.channels.append(channel)
        return True

    def test_channels(self) -> Dict[str, bool]:
        """Test all configured channels"""
        results = {}
        for i, channel in enumerate(self.channels):
            channel_name = channel.__class__.__name__
            results[f"{channel_name}_{i}"] = channel.test_connection()
        return results

    def fire_alert(
        self,
        alert_key: str,
        title: str,
        description: str,
        primary_reason: str,
        affected_requests: int,
        metrics: Dict,
        severity: AlertSeverity = AlertSeverity.WARNING,
    ) -> bool:
        """
        Fire an alert

        Args:
            alert_key: Unique key for alert deduplication
            title: Alert title
            description: Detailed description
            primary_reason: Main reason for alert
            affected_requests: Number of affected requests
            metrics: Relevant metrics
            severity: Alert severity

        Returns:
            True if alert was sent, False if rate-limited or already active
        """

        # Check if alert already active
        if alert_key in self.active_alerts:
            return False

        # Check rate limit
        if alert_key in self.last_alert_time:
            time_since_last = time.time() - self.last_alert_time[alert_key]
            if time_since_last < self.rate_limit_seconds:
                return False

        # Create alert
        alert = Alert(
            alert_id=alert_key,
            severity=severity,
            title=title,
            description=description,
            timestamp=time.time(),
            model_name=self.model_name,
            environment=self.environment,
            primary_reason=primary_reason,
            affected_requests=affected_requests,
            metrics=metrics,
        )

        # Send to all channels
        success = True
        for channel in self.channels:
            try:
                channel.send_alert(alert)
            except Exception as e:
                print(f"Failed to send alert via {channel.__class__.__name__}: {e}")
                success = False

        # Track alert
        self.active_alerts[alert_key] = alert
        self.last_alert_time[alert_key] = time.time()
        self.alerts_sent += 1

        return success

    def resolve_alert(self, alert_key: str) -> bool:
        """Resolve an active alert"""

        if alert_key not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_key]
        alert.is_resolved = True
        alert.resolved_at = time.time()

        # Send resolution to all channels
        for channel in self.channels:
            try:
                channel.send_alert(alert)
            except Exception as e:
                print(f"Failed to send resolution via {channel.__class__.__name__}: {e}")

        # Remove from active alerts
        del self.active_alerts[alert_key]
        self.alerts_resolved += 1

        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_statistics(self) -> Dict:
        """Get alert statistics"""
        return {
            "alerts_sent": self.alerts_sent,
            "alerts_resolved": self.alerts_resolved,
            "active_alerts": len(self.active_alerts),
            "channels_configured": len(self.channels),
        }
