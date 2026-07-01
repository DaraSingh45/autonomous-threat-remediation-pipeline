

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Building and starting all services (this can take a couple of minutes the first time)"
docker compose up --build -d

echo "==> Waiting for Kafka to report healthy"
until [ "$(docker inspect -f '{{.State.Health.Status}}' atrp-kafka 2>/dev/null)" = "healthy" ]; do
  sleep 2
  echo "    still waiting on Kafka..."
done

echo "==> Waiting for the audit service to come up"
until curl -sf http://localhost:8090/health >/dev/null 2>&1; do
  sleep 2
done

cat <<'EOF'

==> Stack is up. The event generator is already producing synthetic
    telemetry and attacks are being detected + remediated autonomously.

    Grafana (dashboards, admin/admin):   http://localhost:3000
    Prometheus (raw metrics):            http://localhost:9090
    Audit trail (JSON):                  http://localhost:8090/audit
    Audit stats (MTTD/MTTR by mode):     http://localhost:8090/stats
    Mock IAM service:                    http://localhost:8080/users

To see the "before automation" MTTR baseline, edit the AUTONOMOUS_MODE
env var for decision-engine in docker-compose.yml to "false", then:
    docker compose up -d --build decision-engine

To stop everything:
    docker compose down -v
EOF
