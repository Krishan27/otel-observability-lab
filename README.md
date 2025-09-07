# otel-observability-lab
Minimal, interview-ready lab that shows **OpenTelemetry on Kubernetes** with:
- **Python FastAPI** app (auto-instrumented)
- **OpenTelemetry Collector (Gateway)**
- **Docker Compose** (local dev) **or** **Kind + Helm** (local K8s)
- **GitHub Actions CI** (tests → build/push → Helm render)
- **GitHub Actions CD** (spin up Kind in CI → deploy → smoke test)
- **Resiliency drills** (queue/retry, batching, memory limiter, tail sampling)

> Goal: demonstrate vendor-agnostic telemetry: **SDK → OTLP → Collector → exporter(s)** with safe rollouts and clear ops story.

---

## 📦 Repository layout

```
otel-observability-lab/
├─ .github/workflows/
│ ├─ ci.yml # M5: tests + build/push (GHCR) + helm template
│ └─ cd-kind.yml # M6: ephemeral Kind deploy + smoke test + logs
├─ collector/dev/otel-collector.yaml # M2: dev collector for Docker Compose (debug exporter)
├─ docker-compose.yml # M2: run app+collector locally (no K8s)
├─ helm/
│ ├─ api/ # App chart
│ │ ├─ Chart.yaml
│ │ ├─ values.yaml # defaults
│ │ ├─ values-dev.yaml # env overrides
│ │ ├─ values-prod.yaml
│ │ └─ templates/{deployment.yaml,service.yaml}
│ └─ otel-gateway/ # Collector Gateway chart
│ ├─ Chart.yaml
│ ├─ values.yaml # defaults (dev)
│ ├─ values-dev.yaml
│ ├─ values-prod.yaml # prod turns on tail sampling
│ └─ templates/{deployment.yaml,service.yaml,configmap.yaml}
├─ scripts/
│ ├─ deploy-kind-dev.sh # one-shot: build+load image, helm install dev
│ └─ destroy-kind.sh
├─ services/api/
│ ├─ Dockerfile
│ ├─ requirements.txt
│ ├─ app/main.py # FastAPI with error/slow endpoints
│ └─ tests/test_health.py # tiny pytest
└─ docs/ (optional) # diagram, runbook, screenshots

```

---

## 🚀 Quick start

You can run this lab in **two ways**. Pick one.

### Option A — Docker Compose (fastest)

Prereqs: Docker Desktop.

```bash
docker compose up --build
# in another terminal:
curl http://localhost:8001/health
curl http://localhost:8001/work
curl http://localhost:8001/error
# see spans/logs in collector output:
docker compose logs -f otel-collector
The dev collector uses the debug exporter (because logging is deprecated) so you can see telemetry in the container logs.

Option B — Kind + Helm (local Kubernetes)

Prereqs (macOS with Homebrew; Intel path shown):

# once
 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile && source ~/.zprofile
brew install kind kubernetes-cli helm


Create cluster + namespace:

kind create cluster --name otel-lab
kubectl config use-context kind-otel-lab
kubectl create ns o11y || true


Build & load the app image into Kind (important!):

docker build -t otel-observability-lab-api:dev ./services/api
kind load docker-image otel-observability-lab-api:dev --name otel-lab


Install collector (dev) then app:

helm upgrade --install otel-gateway ./helm/otel-gateway -n o11y -f ./helm/otel-gateway/values-dev.yaml
helm upgrade --install api          ./helm/api          -n o11y -f ./helm/api/values-dev.yaml --set image.tag=dev

kubectl -n o11y rollout status deploy/otel-gateway
kubectl -n o11y rollout status deploy/api


Test & observe:

kubectl -n o11y port-forward svc/api 8001:8001
# new terminal
curl http://localhost:8001/health
curl http://localhost:8001/work
curl http://localhost:8001/error

# collector shows telemetry via debug exporter
kubectl -n o11y logs -l app=otel-gateway -f

(Optional) “Prod” demo with tail sampling
helm upgrade --install otel-gateway ./helm/otel-gateway -n o11y -f ./helm/otel-gateway/values-prod.yaml
kubectl -n o11y rollout status deploy/otel-gateway

# Tail-sampling triggers on errors/slow (>500ms):
curl "http://localhost:8001/work?ms=600"
curl "http://localhost:8001/error"

🧩 What’s instrumented

App: FastAPI auto-instrumented via CLI (opentelemetry-instrument uvicorn …)
Env:

OTEL_TRACES/LOGS/METRICS_EXPORTER=otlp

OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-gateway:4318

OTEL_PYTHON_LOG_CORRELATION=true → logs include trace_id / span_id.

Collector (Gateway):

Dev: exporters.debug so you can see data in logs.

Prod: adds tail sampling (ERROR + slow traces) and higher replica count.

Processors order: attributes → transform/redaction (if enabled) → [tailsampling prod] → batch → memory_limiter.