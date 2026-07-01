# Setup Guide

## Prerequisites

| Tool | Needed for | Install |
|---|---|---|
| Docker + Docker Compose v2 | Local demo (`docker compose up`) | https://docs.docker.com/get-docker/ |
| `kubectl` | Kubernetes deployment | https://kubernetes.io/docs/tasks/tools/ |
| `kind` **or** `minikube` | A local Kubernetes cluster to deploy into | https://kind.sigs.k8s.io/ / https://minikube.sigs.k8s.io/ |
| Python 3.12 | Running tests / retraining the model outside Docker | https://www.python.org/downloads/ |

You do **not** need a Kubernetes cluster to run the full pipeline end-to-end — `docker compose up` is enough; the Remediation Agent defaults to `K8S_MODE=simulated` and logs what it *would* have done to a cluster. A real cluster is only needed to see it actually isolate a real pod (see [Kubernetes deployment](#kubernetes-deployment) below).

## Local demo (Docker Compose)

```bash
git clone <your-fork-url>
cd autonomous-threat-remediation-pipeline
cp .env.example .env        # optional - defaults already work
docker compose up --build
```

Or use the helper script, which also waits for health checks and prints the URLs:

```bash
./scripts/run_local_demo.sh
```

Once it's up:

| What | Where |
|---|---|
| Grafana (dashboards) | http://localhost:3000 (`admin` / `admin`, or anonymous viewer access is enabled) |
| Prometheus (raw metrics) | http://localhost:9090 |
| Audit trail (JSON) | http://localhost:8090/audit |
| Audit stats by mode | http://localhost:8090/stats |
| Mock IAM identities | http://localhost:8080/users |

Within a few seconds you should see `events_produced_total` climbing in Prometheus, and within a couple of minutes (attack bursts are injected with ~8% probability per tick) the Grafana dashboard should show detections and remediation actions. To force one immediately, see [Triggering a specific attack](#triggering-a-specific-attack-on-demand) below.

To stop everything (and remove the audit DB / Grafana volumes):

```bash
docker compose down -v
```

## Seeing the "before vs. after automation" comparison

By default `AUTONOMOUS_MODE=true`: detections are remediated immediately. To generate the manual-baseline comparison data as well:

```bash
# Edit docker-compose.yml: set decision-engine's AUTONOMOUS_MODE to "false"
docker compose up -d --build decision-engine
# let it run for a few minutes, then flip it back to "true" and rebuild again
```

Grafana's "MTTR - Autonomous vs Manual (Simulated Baseline)" panel plots both `mode="autonomous"` and `mode="manual_simulated"` series once both have data, so running each mode for a few minutes gives you a real, measured before/after comparison rather than a hardcoded number.

## Triggering a specific attack on demand

The event generator injects a random scenario from `services/event_generator/scenarios.py` with `ATTACK_PROBABILITY` (default 8%) chance per tick. To watch one happen live without waiting:

```bash
# tail detection + decision + remediation logs together
docker compose logs -f detection-engine decision-engine remediation-agent

# or bump the attack probability temporarily for a livelier demo
docker compose stop event-generator
docker compose run --rm -e ATTACK_PROBABILITY=0.5 event-generator
```

## Kubernetes deployment

This shows the pipeline actually running on a cluster, with the Remediation Agent's RBAC-scoped ServiceAccount really isolating a real pod.

### 1. Create a cluster

```bash
# kind
kind create cluster --name atrp

# OR minikube
minikube start --cpus=4 --memory=8192
```

### 2. Deploy

```bash
./scripts/deploy_k8s.sh kind       # or: ./scripts/deploy_k8s.sh minikube
```

This builds all six service images, loads them into the cluster, creates the `security-pipeline` and `demo-workloads` namespaces, applies RBAC, deploys Kafka + all services, generates the Prometheus/Grafana ConfigMaps from the same files used by docker-compose, and waits for every Deployment to become ready.

### 3. Watch it work

```bash
kubectl -n security-pipeline get pods
kubectl -n demo-workloads get pods --show-labels     # watch for quarantine=true appearing
kubectl -n demo-workloads get networkpolicies         # watch deny-all policies appear

kubectl -n security-pipeline logs -f deployment/remediation-agent
```

### 4. Open the dashboards

```bash
kubectl -n security-pipeline port-forward svc/grafana 3000:3000 &
kubectl -n security-pipeline port-forward svc/audit-service 8090:8090 &
```

### 5. Tear down

```bash
make k8s-clean
# or: kubectl delete namespace security-pipeline demo-workloads
```

## Running tests / retraining the model outside Docker

```bash
make install     # creates .venv and installs every service's requirements + dev tools
make test        # pytest
make lint        # ruff
make train-model # regenerate services/detection_engine/models/isolation_forest.pkl
make proto       # regenerate gRPC stubs after editing proto/pipeline.proto
```

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `detection-engine` / `decision-engine` / `audit-service` crash-loop on first `docker compose up` | Kafka takes ~15-20s to finish forming its cluster metadata even after its healthcheck passes. Every service retries its own Kafka connection for up to 60s (see `services/common/kafka_utils.wait_for_kafka`) - if it still fails, run `docker compose logs kafka` to check the broker actually started. |
| Remediation Agent logs `[SIMULATED] ...` even though you expected real cluster actions | `K8S_MODE` defaults to `simulated` in docker-compose (by design, so no cluster is required). Set it to `real` and mount a kubeconfig, or use the Kubernetes deployment path above where the ConfigMap already sets `K8S_MODE=real`. |
| `kind load docker-image` fails with "no nodes found" | Your kind cluster isn't named `kind` (the default `kind create cluster` name). Pass `--name` consistently, or edit `scripts/deploy_k8s.sh`. |
| Grafana shows "No data" on the MTTR panel | No detections have completed yet in that mode. Wait for an attack burst (or lower `ATTACK_PROBABILITY`'s denominator by raising it, see above) and make sure you've generated data in both `AUTONOMOUS_MODE` states if you want the comparison panel populated for both series. |
