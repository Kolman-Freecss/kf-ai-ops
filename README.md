# 🔮 AI-Ops Platform

A modern intelligent operations platform combining **observability**, **infrastructure as code**, and **AI-powered automation**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI-Ops Platform                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │   App API    │───▶│ OpenTelemetry│───▶│  Observability Stack │   │
│  │  (FastAPI)   │    │   Collector  │    │  (Traces/Metrics)    │   │
│  └──────────────┘    └──────────────┘    └──────────────────────┘   │
│         │                                           │                │
│         ▼                                           ▼                │
│  ┌──────────────┐                        ┌──────────────────────┐   │
│  │   OpenTofu   │                        │    AI Analyzer       │   │
│  │Infrastructure│                        │ (Pipeline Optimizer) │   │
│  └──────────────┘                        └──────────────────────┘   │
│         │                                           │                │
│         ▼                                           ▼                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              GitHub Actions (Self-Optimizing CI/CD)           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 📦 Components

| Component | Description | Technology |
|-----------|-------------|------------|
| **App API** | Sample service with observability | FastAPI + OpenTelemetry |
| **Infrastructure** | Declarative infrastructure | OpenTofu |
| **AI Analyzer** | Analysis and optimization engine | Python + OpenAI |
| **CI/CD** | Self-optimizing pipelines | GitHub Actions |

## 🚀 Quick Start

### Requirements

- Python 3.11+
- OpenTofu 1.6+
- Docker (optional)

### Setup

```bash
# Clone and enter project
cd kf-ai-ops

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r app/requirements.txt

# Environment variables
cp .env.example .env
```

### Run the application

```bash
# Development mode
cd app
uvicorn main:app --reload --port 8000

# With Docker
docker compose up -d
```

### Deploy infrastructure

```bash
cd infrastructure
tofu init
tofu plan
tofu apply
```

## 🔍 OpenTelemetry

The application is instrumented with OpenTelemetry to capture:

- **Traces**: Distributed request tracing
- **Metrics**: Latency, throughput, errors
- **Logs**: Structured logs correlated with traces

```python
# Custom span example
with tracer.start_as_current_span("critical_process") as span:
    span.set_attribute("user.id", user_id)
    result = execute_process()
    span.set_attribute("result.status", "success")
```

## 🤖 AI Pipeline Optimizer

The pipeline optimizer analyzes GitHub Actions execution and suggests improvements:

```yaml
# The workflow analyzes its own execution
- name: AI Pipeline Analysis
  uses: ./.github/actions/ai-optimizer
  with:
    analyze: true
    auto-optimize: true
```

**Capabilities:**
- Detects jobs that can be parallelized
- Suggests dependency caching
- Identifies redundant steps
- Optimizes testing matrices

## 📊 Key Metrics

The dashboard displays real-time metrics:

| Metric | Description |
|--------|-------------|
| `pipeline.duration` | Total pipeline duration |
| `pipeline.success_rate` | Success rate |
| `ai.optimizations_applied` | Applied optimizations |
| `infra.resources_managed` | OpenTofu resources |

## 📁 Project Structure

```
kf-ai-ops/
├── app/                    # Application with OpenTelemetry
│   ├── main.py
│   ├── telemetry.py
│   └── requirements.txt
├── infrastructure/         # OpenTofu modules
│   ├── main.tf
│   ├── variables.tf
│   └── modules/
├── ai-optimizer/           # AI engine
│   ├── analyzer.py
│   └── optimizer.py
├── .github/
│   └── workflows/          # Smart GitHub Actions
└── dashboard/              # Visualization UI
```

## 🔧 Configuration

### Environment Variables

```bash
# OpenTelemetry
OTEL_SERVICE_NAME=ai-ops-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# AI Optimizer
OPENAI_API_KEY=sk-...
AI_OPTIMIZER_ENABLED=true

# OpenTofu
TF_VAR_environment=development
```

## 📈 Optimization Flow

```
1. Push to repository
        │
        ▼
2. GitHub Action runs
        │
        ▼
3. AI Analyzer collects metrics
        │
        ▼
4. Model analyzes patterns
        │
        ▼
5. Generates optimization suggestions
        │
        ▼
6. (Optional) Applies changes automatically
```

## 🛠️ Development

```bash
# Tests
pytest app/tests/

# Linting
ruff check .

# Type checking
mypy app/
```

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.
