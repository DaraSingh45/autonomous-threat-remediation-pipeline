.PHONY: help venv install test lint proto train-model up down demo logs clean k8s-deploy k8s-clean

help:
	@echo "Autonomous Threat Remediation Pipeline"
	@echo ""
	@echo "  make venv          create a local Python venv for development"
	@echo "  make install       install all service requirements + dev tools into the venv"
	@echo "  make test          run the unit test suite"
	@echo "  make lint          run ruff over services/ and tests/"
	@echo "  make proto         regenerate gRPC stubs from proto/pipeline.proto"
	@echo "  make train-model   retrain the Isolation Forest and overwrite the shipped .pkl"
	@echo "  make up            docker compose up --build (local demo)"
	@echo "  make demo          scripts/run_local_demo.sh (build, wait, print URLs)"
	@echo "  make down          docker compose down -v"
	@echo "  make logs          tail logs from all services"
	@echo "  make k8s-deploy    build images and deploy to a local kind/minikube cluster"
	@echo "  make k8s-clean     delete the pipeline namespaces from the current kube-context"
	@echo "  make clean         remove venv, caches, and __pycache__ directories"

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r services/event_generator/requirements.txt
	$(PIP) install -r services/detection_engine/requirements.txt
	$(PIP) install -r services/decision_engine/requirements.txt
	$(PIP) install -r services/remediation_agent/requirements.txt
	$(PIP) install -r services/mock_iam_service/requirements.txt
	$(PIP) install -r services/audit_service/requirements.txt
	$(PIP) install pytest ruff grpcio-tools

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check services tests

proto:
	$(PYTHON) -m grpc_tools.protoc -I proto \
		--python_out=proto/generated/python \
		--grpc_python_out=proto/generated/python \
		--pyi_out=proto/generated/python \
		proto/pipeline.proto

train-model:
	PYTHONPATH=. $(PYTHON) -m services.detection_engine.train_isolation_forest

up:
	docker compose up --build -d

demo:
	./scripts/run_local_demo.sh

down:
	docker compose down -v

logs:
	docker compose logs -f

k8s-deploy:
	./scripts/deploy_k8s.sh kind

k8s-clean:
	kubectl delete namespace security-pipeline demo-workloads --ignore-not-found

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
