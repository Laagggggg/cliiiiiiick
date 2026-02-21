from __future__ import annotations


def build_alert(channel: str, title: str, body: str, severity: str = "INFO") -> dict:
    return {
        "channel": channel,
        "title": title,
        "body": body,
        "severity": severity.upper(),
    }


def should_alert_drift(psi: float, threshold: float = 0.20) -> bool:
    return psi > threshold
