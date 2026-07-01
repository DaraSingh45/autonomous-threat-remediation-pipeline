

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

python -m grpc_tools.protoc \
  -I proto \
  --python_out=proto/generated/python \
  --grpc_python_out=proto/generated/python \
  --pyi_out=proto/generated/python \
  proto/pipeline.proto

echo "Regenerated proto/generated/python/pipeline_pb2*.py"
