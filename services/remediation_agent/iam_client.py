"""
Client for the Mock IAM Service.

Stands in for calling a real identity provider's admin API (Okta, Azure
AD, AWS IAM) to disable a compromised account/session. Talking REST here
(rather than gRPC) is deliberate: this is exactly the kind of boundary in
a real environment where you're integrating with a third-party system you
don't control the protocol for.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from services.common.logging_config import get_logger

logger = get_logger("remediation_agent.iam_client")

MOCK_IAM_URL = os.environ.get("MOCK_IAM_URL", "http://mock-iam-service:8080")


@dataclass
class IamActionResult:
    success: bool
    details: str


def revoke_credential(user_id: str, reason: str) -> IamActionResult:
    try:
        resp = requests.post(
            f"{MOCK_IAM_URL}/revoke/{user_id}",
            json={"reason": reason},
            timeout=5,
        )
        if resp.status_code == 404:
            return IamActionResult(success=False, details=f"unknown user '{user_id}' in mock IAM")
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Revoked credentials for user={user_id}")
        return IamActionResult(success=True, details=f"credentials revoked for '{user_id}': {data.get('status')}")
    except requests.RequestException as exc:
        logger.error(f"Mock IAM call failed for user={user_id}: {exc}")
        return IamActionResult(success=False, details=f"mock IAM call failed: {exc}")
