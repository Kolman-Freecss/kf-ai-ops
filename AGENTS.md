# Repository Guidelines

## Project Structure & Ownership
- `app/`: FastAPI service with OpenTelemetry (`main.py`, `telemetry.py`, tests in `app/tests/`).
- `ai-optimizer/`: Pipeline analysis and workflow optimization scripts.
- `infrastructure/`: OpenTofu modules and stacks; run `tofu` commands here.
- `dashboard/`: Static dashboard (`index.html`) surfaced by Docker Compose.
- Root configs: `pyproject.toml` (ruff, pytest, coverage, mypy), `docker-compose.yml`, `otel-collector-config.yml`, `prometheus.yml`, `Makefile` helpers.

## Setup & Development Flow
- Create a venv and install deps: `make setup-venv && source .venv/bin/activate && make install`.
- Local API dev: `make dev` (serves on `:8000`, hot reload).
- Docker stack: `make docker-up` / `make docker-down` to run API, telemetry, and dashboard.
- Infra: from `infrastructure/`, run `make infra-init`, `make infra-plan`, `make infra-apply` as needed.

## Build, Test, and Verification
- `make test`: run all pytest suites in `app/tests/`.
- `make test-unit` / `make test-integration`: targeted markers (`-m unit` / `-m integration`).
- `make lint`: ruff lint across `app/` and `ai-optimizer/`.
- `make format`: ruff format for Python sources.
- `make optimize`: run the AI analyzer; `make optimize-workflow` targets a specific workflow file.
- `make check`: lint + tests; use before PRs.

## Coding Style & Naming
- Python 3.11+, 4-space indents, 100-char lines, double quotes preferred (ruff formatter enforces).
- Keep functions small; prefer explicit imports; first-party modules marked as `app`/`ai_optimizer` in isort config.
- Test files: `test_*.py`; test functions: `test_*`; use `@pytest.mark.unit` / `@pytest.mark.integration`.

## Testing Expectations
- Add/extend tests in `app/tests/` for new endpoints, telemetry hooks, and optimizer behaviors.
- Aim to cover happy path + failure branches; prefer deterministic fixtures over sleeps.
- If adding slow/external tests, mark with `@pytest.mark.slow` so they can be skipped by default.

## Git Hygiene & Pull Requests
- Commit messages: short present-tense summary (optionally `type: summary`, e.g., `feat: add OTLP exporter config`). Current history is minimal—keep it clean and descriptive.
- PRs should include: purpose, key changes, test evidence (`make check` output), and any config/env var impacts.
- Link issues or tickets where applicable; include screenshots or curl examples for API/UI changes when helpful.

## Security & Configuration
- Do not commit secrets; use `.env` (see `.env.example`) and environment variables for keys like `OPENAI_API_KEY`.
- Validate telemetry endpoints before enabling exports; use `otel-collector-config.yml` and `prometheus.yml` as baselines, not production defaults.
- For infra changes, run `make infra-plan` and share the diff in PR descriptions.
