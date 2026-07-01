

set -euo pipefail

CLUSTER_TYPE="${1:-kind}"
IMAGES=(event-generator detection-engine decision-engine remediation-agent mock-iam-service audit-service)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Building images"
for svc in "${IMAGES[@]}"; do
  dir="services/${svc//-/_}"
  echo "    building atrp/${svc}:latest from ${dir}/Dockerfile"
  docker build -t "atrp/${svc}:latest" -f "${dir}/Dockerfile" .
done

echo "==> Loading images into the ${CLUSTER_TYPE} cluster"
for svc in "${IMAGES[@]}"; do
  if [ "$CLUSTER_TYPE" = "kind" ]; then
    kind load docker-image "atrp/${svc}:latest"
  elif [ "$CLUSTER_TYPE" = "minikube" ]; then
    minikube image load "atrp/${svc}:latest"
  else
    echo "Unknown cluster type '${CLUSTER_TYPE}' (expected 'kind' or 'minikube')" >&2
    exit 1
  fi
done

echo "==> Creating namespaces"
kubectl apply -f k8s/base/namespace.yaml

echo "==> Deploying demo workload pods (remediation targets)"
kubectl apply -f k8s/demo-workloads/sample-pods.yaml

echo "==> Applying RBAC + shared config"
kubectl apply -f k8s/base/rbac.yaml
kubectl apply -f k8s/base/configmap.yaml

echo "==> Deploying Kafka"
kubectl apply -f k8s/base/kafka.yaml
kubectl -n security-pipeline rollout status deployment/kafka --timeout=120s

echo "==> Deploying pipeline services"
kubectl apply -f k8s/base/mock-iam-service.yaml
kubectl apply -f k8s/base/remediation-agent.yaml
kubectl apply -f k8s/base/decision-engine.yaml
kubectl apply -f k8s/base/detection-engine.yaml
kubectl apply -f k8s/base/event-generator.yaml
kubectl apply -f k8s/base/audit-service.yaml

echo "==> Loading monitoring config from repo files into ConfigMaps"
kubectl -n security-pipeline create configmap prometheus-config \
  --from-file=monitoring/prometheus/prometheus.yml \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n security-pipeline create configmap grafana-datasources \
  --from-file=monitoring/grafana/provisioning/datasources \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n security-pipeline create configmap grafana-dashboard-provisioning \
  --from-file=monitoring/grafana/provisioning/dashboards \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n security-pipeline create configmap grafana-dashboards \
  --from-file=monitoring/grafana/dashboards \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Deploying Prometheus + Grafana"
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml

echo "==> Waiting for core deployments to become ready"
for dep in mock-iam-service remediation-agent decision-engine detection-engine event-generator audit-service prometheus grafana; do
  kubectl -n security-pipeline rollout status "deployment/${dep}" --timeout=120s
done

cat <<'EOF'

==> Deployed. Try:
    kubectl -n security-pipeline get pods
    kubectl -n demo-workloads get pods -l quarantine=true    # watch remediation happen live
    kubectl -n security-pipeline port-forward svc/grafana 3000:3000
    kubectl -n security-pipeline port-forward svc/audit-service 8090:8090

Remember: this deployment sets K8S_MODE=real (see k8s/base/configmap.yaml), so
the Remediation Agent will actually label + NetworkPolicy-isolate the demo
pods in k8s/demo-workloads when it detects a high/critical severity threat.
EOF
