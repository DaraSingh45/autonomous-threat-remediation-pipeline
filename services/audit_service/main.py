import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from services.audit_service import db
from services.common.kafka_utils import build_consumer, wait_for_kafka
from services.common.logging_config import get_logger

logger = get_logger("audit_service")

AUDIT_TOPIC = os.environ.get("AUDIT_TOPIC", "audit-log")

AUDIT_RECORDS_STORED = Counter("audit_records_stored_total", "Audit records persisted", ["mode", "action"])
MTTD_SECONDS = Histogram(
    "mttd_seconds", "Mean-time-to-detect: event occurrence to detection", ["mode"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)
MTTR_SECONDS = Histogram(
    "mttr_seconds", "Mean-time-to-remediate: detection to remediation complete", ["mode"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
)

_conn = db.get_connection()
db.init_db(_conn)
_stop_flag = False


def _consume_loop():
    wait_for_kafka()
    consumer = build_consumer(topics=[AUDIT_TOPIC], group_id="audit-service")
    logger.info(f"Audit Service consuming from '{AUDIT_TOPIC}'")
    while not _stop_flag:
        for message in consumer:
            try:
                record = message.value
                db.insert_record(_conn, record)
                AUDIT_RECORDS_STORED.labels(mode=record["mode"], action=record["action"]).inc()
                if record.get("mttd_ms") is not None:
                    MTTD_SECONDS.labels(mode=record["mode"]).observe(record["mttd_ms"] / 1000.0)
                if record.get("mttr_ms") is not None:
                    MTTR_SECONDS.labels(mode=record["mode"]).observe(record["mttr_ms"] / 1000.0)
            except Exception:
                logger.exception("Failed to persist audit record; continuing")
            if _stop_flag:
                break


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_consume_loop, daemon=True)
    thread.start()
    yield
    global _stop_flag
    _stop_flag = True


app = FastAPI(title="Audit Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/audit")
def list_audit(limit: int = 50, offset: int = 0):
    limit = max(1, min(limit, 500))
    return {"records": db.list_records(_conn, limit=limit, offset=offset)}


@app.get("/audit/{audit_id}")
def get_audit(audit_id: str):
    record = db.get_record(_conn, audit_id)
    if not record:
        raise HTTPException(status_code=404, detail="audit record not found")
    return record


@app.get("/stats")
def stats():
    return {"by_mode": db.stats_by_mode(_conn)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8090)))
