"""
AI-Ops API - Main service with OpenTelemetry observability.
"""

import time
import random
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from opentelemetry import trace

from telemetry import get_telemetry


# Data models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class PipelineMetrics(BaseModel):
    pipeline_id: str
    duration_ms: float
    steps_count: int
    success: bool
    optimizations_suggested: int


class OptimizationRequest(BaseModel):
    pipeline_config: dict
    metrics_history: list[dict] | None = None


class OptimizationResponse(BaseModel):
    suggestions: list[dict]
    estimated_improvement: float
    confidence: float


# Lifespan for initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    telemetry = get_telemetry()
    telemetry.instrument_app(app)
    telemetry.logger.info("application_started")
    yield
    # Shutdown
    telemetry.logger.info("application_shutdown")


# Create application
app = FastAPI(
    title="AI-Ops API",
    description="Intelligent operations API with observability",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    telemetry = get_telemetry()
    telemetry.active_requests.add(1)
    
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start_time) * 1000
    
    telemetry.request_counter.add(1, {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
    })
    
    telemetry.request_duration.record(duration, {
        "method": request.method,
        "path": request.url.path,
    })
    
    telemetry.active_requests.add(-1)
    
    return response


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health status."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


@app.get("/metrics/pipeline/{pipeline_id}", response_model=PipelineMetrics)
async def get_pipeline_metrics(pipeline_id: str):
    """Get metrics for a specific pipeline."""
    telemetry = get_telemetry()
    tracer = telemetry.tracer
    
    with tracer.start_as_current_span("fetch_pipeline_metrics") as span:
        span.set_attribute("pipeline.id", pipeline_id)
        
        # Simulate fetching metrics
        await simulate_database_query()
        
        metrics = PipelineMetrics(
            pipeline_id=pipeline_id,
            duration_ms=random.uniform(30000, 180000),
            steps_count=random.randint(5, 15),
            success=random.random() > 0.1,
            optimizations_suggested=random.randint(0, 5),
        )
        
        span.set_attribute("pipeline.duration_ms", metrics.duration_ms)
        span.set_attribute("pipeline.success", metrics.success)
        
        telemetry.logger.info(
            "pipeline_metrics_fetched",
            pipeline_id=pipeline_id,
            duration_ms=metrics.duration_ms,
        )
        
        return metrics


@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_pipeline(request: OptimizationRequest):
    """Analyze a pipeline and suggest AI-powered optimizations."""
    telemetry = get_telemetry()
    tracer = telemetry.tracer
    
    with tracer.start_as_current_span("ai_optimization") as span:
        span.set_attribute("optimization.type", "pipeline")
        
        # Analyze pipeline configuration
        suggestions = await analyze_pipeline_config(request.pipeline_config)
        
        # Record optimization
        telemetry.ai_optimizations.add(len(suggestions))
        
        response = OptimizationResponse(
            suggestions=suggestions,
            estimated_improvement=random.uniform(10, 40),
            confidence=random.uniform(0.7, 0.95),
        )
        
        span.set_attribute("optimization.suggestions_count", len(suggestions))
        span.set_attribute("optimization.estimated_improvement", response.estimated_improvement)
        
        telemetry.logger.info(
            "optimization_completed",
            suggestions_count=len(suggestions),
            estimated_improvement=response.estimated_improvement,
        )
        
        return response


@app.get("/traces/summary")
async def get_traces_summary():
    """Get a summary of recent traces."""
    telemetry = get_telemetry()
    
    with telemetry.tracer.start_as_current_span("get_traces_summary"):
        # In production, this would query the traces backend
        return {
            "total_traces": random.randint(100, 1000),
            "avg_duration_ms": random.uniform(50, 200),
            "error_rate": random.uniform(0.01, 0.05),
            "top_endpoints": [
                {"path": "/health", "count": random.randint(500, 1000)},
                {"path": "/optimize", "count": random.randint(100, 500)},
                {"path": "/metrics/pipeline", "count": random.randint(50, 200)},
            ],
        }


@app.get("/infrastructure/status")
async def get_infrastructure_status():
    """Get status of infrastructure managed by OpenTofu."""
    telemetry = get_telemetry()
    
    with telemetry.tracer.start_as_current_span("get_infra_status") as span:
        # Simulate querying OpenTofu state
        status = {
            "managed_resources": random.randint(10, 50),
            "last_apply": datetime.utcnow().isoformat(),
            "drift_detected": random.random() < 0.1,
            "modules": [
                {"name": "networking", "resources": 5, "status": "applied"},
                {"name": "compute", "resources": 3, "status": "applied"},
                {"name": "observability", "resources": 8, "status": "applied"},
            ],
        }
        
        span.set_attribute("infra.resources_count", status["managed_resources"])
        span.set_attribute("infra.drift_detected", status["drift_detected"])
        
        return status


# Helper functions
async def simulate_database_query():
    """Simulate a database query with latency."""
    telemetry = get_telemetry()
    
    with telemetry.tracer.start_as_current_span("database_query") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "SELECT")
        
        # Simulate DB latency
        delay = random.uniform(0.01, 0.05)
        time.sleep(delay)
        
        span.set_attribute("db.duration_ms", delay * 1000)


async def analyze_pipeline_config(config: dict) -> list[dict]:
    """Analyze pipeline configuration and generate suggestions."""
    telemetry = get_telemetry()
    
    with telemetry.tracer.start_as_current_span("analyze_config") as span:
        suggestions = []
        
        # Analysis-based suggestions
        possible_suggestions = [
            {
                "type": "cache",
                "title": "Add dependency caching",
                "description": "Caching node_modules/pip packages would reduce ~2min",
                "impact": "high",
            },
            {
                "type": "parallel",
                "title": "Parallelize test jobs",
                "description": "Tests can run in parallel using matrix strategy",
                "impact": "high",
            },
            {
                "type": "skip",
                "title": "Conditional step skipping",
                "description": "Skip linting if no source code changes detected",
                "impact": "medium",
            },
            {
                "type": "runner",
                "title": "Use more powerful runner",
                "description": "A runner with more cores would speed up compilation",
                "impact": "medium",
            },
            {
                "type": "artifact",
                "title": "Optimize artifacts",
                "description": "Compressing artifacts would reduce upload/download time",
                "impact": "low",
            },
        ]
        
        # Select random suggestions for demo
        num_suggestions = random.randint(1, 4)
        suggestions = random.sample(possible_suggestions, num_suggestions)
        
        span.set_attribute("analysis.suggestions_generated", len(suggestions))
        
        return suggestions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
