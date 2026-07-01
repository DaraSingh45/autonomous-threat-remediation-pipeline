

import os
import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel
from starlette.responses import Response

from services.common.logging_config import get_logger

logger = get_logger("mock_iam_service")

app = FastAPI(title="Mock IAM Service", version="1.0.0")

REVOCATIONS = Counter("iam_revocations_total", "Credential revocations processed")
RESTORES = Counter("iam_restores_total", "Credential restores processed")

_lock = threading.Lock()
_users: dict[str, dict] = {
    user_id: {"user_id": user_id, "active": True, "revoked_at": None, "revoked_reason": None}
    for user_id in ["alice", "bob", "carol", "dave", "erin", "svc-payments", "svc-billing"]
}


class RevokeRequest(BaseModel):
    reason: Optional[str] = "automated remediation"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/users")
def list_users():
    with _lock:
        return list(_users.values())


@app.get("/users/{user_id}")
def get_user(user_id: str):
    with _lock:
        user = _users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"unknown user '{user_id}'")
    return user


@app.post("/revoke/{user_id}")
def revoke(user_id: str, body: RevokeRequest = RevokeRequest()):
    with _lock:
        if user_id not in _users:
            # Auto-provision unknown identities rather than hard-failing -
            # keeps the demo resilient to whatever usernames the event
            # generator invents, while still tracking them individually.
            _users[user_id] = {"user_id": user_id, "active": True, "revoked_at": None, "revoked_reason": None}
        _users[user_id]["active"] = False
        _users[user_id]["revoked_at"] = int(time.time() * 1000)
        _users[user_id]["revoked_reason"] = body.reason
        record = dict(_users[user_id])

    REVOCATIONS.inc()
    logger.info(f"Revoked credentials for {user_id}: {body.reason}")
    return {"status": "revoked", "user": record}


@app.post("/restore/{user_id}")
def restore(user_id: str):
    with _lock:
        if user_id not in _users:
            raise HTTPException(status_code=404, detail=f"unknown user '{user_id}'")
        _users[user_id]["active"] = True
        _users[user_id]["revoked_at"] = None
        _users[user_id]["revoked_reason"] = None
        record = dict(_users[user_id])

    RESTORES.inc()
    logger.info(f"Restored credentials for {user_id}")
    return {"status": "restored", "user": record}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
