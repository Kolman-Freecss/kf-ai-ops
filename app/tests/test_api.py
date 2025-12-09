"""
Tests for AI-Ops API.
"""

import pytest
from fastapi.testclient import TestClient


# Fixtures
@pytest.fixture
def client():
    """Test client for the API."""
    from main import app
    return TestClient(app)


# Health Check Tests
class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Health check should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_returns_healthy_status(self, client):
        """Health check should indicate healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_check_includes_version(self, client):
        """Health check should include version."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"


# Pipeline Metrics Tests
@pytest.mark.integration
class TestPipelineMetrics:
    """Tests for pipeline metrics endpoint."""
    
    def test_get_pipeline_metrics_returns_200(self, client):
        """Get pipeline metrics should return 200."""
        response = client.get("/metrics/pipeline/test-pipeline-123")
        assert response.status_code == 200
    
    def test_pipeline_metrics_includes_required_fields(self, client):
        """Metrics should include all required fields."""
        response = client.get("/metrics/pipeline/test-pipeline-123")
        data = response.json()
        
        required_fields = [
            "pipeline_id",
            "duration_ms",
            "steps_count",
            "success",
            "optimizations_suggested"
        ]
        
        for field in required_fields:
            assert field in data, f"Field {field} not found"
    
    def test_pipeline_metrics_has_valid_values(self, client):
        """Metrics should have valid values."""
        response = client.get("/metrics/pipeline/my-pipeline")
        data = response.json()
        
        assert data["pipeline_id"] == "my-pipeline"
        assert data["duration_ms"] > 0
        assert data["steps_count"] > 0
        assert isinstance(data["success"], bool)


# Optimization Tests
@pytest.mark.integration
class TestOptimization:
    """Tests for optimization endpoint."""
    
    def test_optimize_returns_200(self, client):
        """Optimization endpoint should return 200."""
        payload = {
            "pipeline_config": {
                "name": "test-pipeline",
                "jobs": {
                    "build": {"steps": [{"run": "npm install"}]}
                }
            }
        }
        response = client.post("/optimize", json=payload)
        assert response.status_code == 200
    
    def test_optimize_returns_suggestions(self, client):
        """Optimization should return suggestions."""
        payload = {
            "pipeline_config": {
                "name": "test-pipeline",
                "jobs": {}
            }
        }
        response = client.post("/optimize", json=payload)
        data = response.json()
        
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_optimize_includes_confidence(self, client):
        """Response should include confidence level."""
        payload = {"pipeline_config": {}}
        response = client.post("/optimize", json=payload)
        data = response.json()
        
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1


# Traces Tests
@pytest.mark.unit
class TestTracesSummary:
    """Tests for traces summary endpoint."""
    
    def test_traces_summary_returns_200(self, client):
        """Traces summary should return 200."""
        response = client.get("/traces/summary")
        assert response.status_code == 200
    
    def test_traces_summary_includes_statistics(self, client):
        """Summary should include statistics."""
        response = client.get("/traces/summary")
        data = response.json()
        
        assert "total_traces" in data
        assert "avg_duration_ms" in data
        assert "error_rate" in data


# Infrastructure Tests
@pytest.mark.integration
class TestInfrastructureStatus:
    """Tests for infrastructure status endpoint."""
    
    def test_infrastructure_status_returns_200(self, client):
        """Infrastructure status should return 200."""
        response = client.get("/infrastructure/status")
        assert response.status_code == 200
    
    def test_infrastructure_includes_resources(self, client):
        """Status should include managed resources."""
        response = client.get("/infrastructure/status")
        data = response.json()
        
        assert "managed_resources" in data
        assert "modules" in data
        assert isinstance(data["modules"], list)
