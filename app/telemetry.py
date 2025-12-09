"""
OpenTelemetry configuration for complete observability.
Includes traces, metrics, and correlated logs.
"""

import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import structlog


def create_resource() -> Resource:
    """Create resource with service metadata."""
    return Resource.create({
        SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "ai-ops-api"),
        SERVICE_VERSION: os.getenv("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.namespace": "ai-ops",
    })


def setup_tracing(resource: Resource) -> trace.Tracer:
    """Configure distributed tracing system."""
    provider = TracerProvider(resource=resource)
    
    # OTLP exporter (compatible with Jaeger, Tempo, etc.)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    
    # Batch processor for better performance
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    
    # Register as global provider
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(__name__)


def setup_metrics(resource: Resource) -> metrics.Meter:
    """Configure metrics system."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=30000)
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    
    metrics.set_meter_provider(provider)
    
    return metrics.get_meter(__name__)


def setup_logging():
    """Configure structured logging with trace correlation."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_trace_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def add_trace_context(logger, method_name, event_dict):
    """Add trace context to logs for correlation."""
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


class Telemetry:
    """Main class for managing all telemetry."""
    
    def __init__(self):
        self.resource = create_resource()
        self.tracer = setup_tracing(self.resource)
        self.meter = setup_metrics(self.resource)
        self.logger = setup_logging()
        
        # Custom metrics
        self.request_counter = self.meter.create_counter(
            name="http.requests.total",
            description="Total HTTP requests",
            unit="1",
        )
        
        self.request_duration = self.meter.create_histogram(
            name="http.request.duration",
            description="HTTP request duration",
            unit="ms",
        )
        
        self.active_requests = self.meter.create_up_down_counter(
            name="http.requests.active",
            description="Active requests",
            unit="1",
        )
        
        self.ai_optimizations = self.meter.create_counter(
            name="ai.optimizations.total",
            description="Total AI optimizations applied",
            unit="1",
        )
    
    def instrument_app(self, app):
        """Automatically instrument FastAPI application."""
        FastAPIInstrumentor.instrument_app(app)
        RequestsInstrumentor().instrument()
        self.logger.info("telemetry_initialized", service=self.resource.attributes.get(SERVICE_NAME))


# Singleton for global access
_telemetry: Telemetry | None = None


def get_telemetry() -> Telemetry:
    """Get global telemetry instance."""
    global _telemetry
    if _telemetry is None:
        _telemetry = Telemetry()
    return _telemetry
