"""
AI Analyzer - Intelligent pipeline analysis engine.
Analyzes metrics, patterns, and generates optimization suggestions.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import httpx


class OptimizationType(Enum):
    """Supported optimization types."""
    CACHE = "cache"
    PARALLEL = "parallel"
    SKIP_REDUNDANT = "skip_redundant"
    RESOURCE_UPGRADE = "resource_upgrade"
    CONCURRENCY = "concurrency"
    ARTIFACT = "artifact"
    MATRIX = "matrix"


class ImpactLevel(Enum):
    """Impact level of an optimization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PipelineRun:
    """Represents a pipeline execution."""
    run_id: str
    workflow_name: str
    status: str
    conclusion: Optional[str]
    duration_seconds: float
    created_at: datetime
    jobs: list[dict] = field(default_factory=list)
    
    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60


@dataclass
class Optimization:
    """Optimization suggestion."""
    type: OptimizationType
    title: str
    description: str
    impact: ImpactLevel
    confidence: float  # 0-1
    estimated_savings_seconds: float
    affected_jobs: list[str] = field(default_factory=list)
    code_suggestion: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "impact": self.impact.value,
            "confidence": self.confidence,
            "estimated_savings_minutes": self.estimated_savings_seconds / 60,
            "affected_jobs": self.affected_jobs,
            "code_suggestion": self.code_suggestion,
        }


class PipelineAnalyzer:
    """
    Analyzes CI/CD pipelines and generates optimization suggestions.
    
    Uses a combination of rule-based and pattern analysis
    to identify improvement opportunities.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {github_token}"} if github_token else {},
            timeout=30.0
        )
        self._optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> list[dict]:
        """Load optimization rules."""
        return [
            {
                "name": "cache_dependencies",
                "patterns": ["pip install", "npm install", "yarn install", "go mod download"],
                "optimization_type": OptimizationType.CACHE,
                "impact": ImpactLevel.HIGH,
                "savings_range": (60, 180),  # seconds
            },
            {
                "name": "parallel_tests",
                "patterns": ["pytest", "jest", "go test"],
                "optimization_type": OptimizationType.PARALLEL,
                "impact": ImpactLevel.HIGH,
                "savings_range": (120, 300),
            },
            {
                "name": "concurrency_control",
                "patterns": [],
                "optimization_type": OptimizationType.CONCURRENCY,
                "impact": ImpactLevel.MEDIUM,
                "savings_range": (0, 600),  # Depends on cancellations
            },
            {
                "name": "artifact_optimization",
                "patterns": ["upload-artifact", "download-artifact"],
                "optimization_type": OptimizationType.ARTIFACT,
                "impact": ImpactLevel.LOW,
                "savings_range": (10, 60),
            },
        ]
    
    def fetch_workflow_runs(
        self, 
        repo: str, 
        workflow_name: Optional[str] = None,
        limit: int = 20
    ) -> list[PipelineRun]:
        """Get the latest workflow runs."""
        url = f"https://api.github.com/repos/{repo}/actions/runs"
        params = {"per_page": limit}
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            runs = []
            for run in data.get("workflow_runs", []):
                # Calculate duration
                created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (updated - created).total_seconds()
                
                pipeline_run = PipelineRun(
                    run_id=str(run["id"]),
                    workflow_name=run["name"],
                    status=run["status"],
                    conclusion=run.get("conclusion"),
                    duration_seconds=duration,
                    created_at=created,
                )
                
                if workflow_name is None or pipeline_run.workflow_name == workflow_name:
                    runs.append(pipeline_run)
            
            return runs
            
        except httpx.HTTPError as e:
            print(f"Error fetching runs: {e}")
            return []
    
    def analyze_workflow_config(self, config: dict) -> list[Optimization]:
        """Analyze workflow configuration and generate optimizations."""
        optimizations = []
        
        jobs = config.get("jobs", {})
        
        # Cache analysis
        if not self._has_cache_action(config):
            optimizations.append(Optimization(
                type=OptimizationType.CACHE,
                title="Add dependency caching",
                description="No actions/cache usage detected. Caching dependencies can significantly reduce build time.",
                impact=ImpactLevel.HIGH,
                confidence=0.95,
                estimated_savings_seconds=120,
                code_suggestion=self._generate_cache_suggestion(config),
            ))
        
        # Concurrency analysis
        if "concurrency" not in config:
            optimizations.append(Optimization(
                type=OptimizationType.CONCURRENCY,
                title="Add concurrency control",
                description="Configure concurrency to cancel previous runs on the same PR.",
                impact=ImpactLevel.MEDIUM,
                confidence=0.90,
                estimated_savings_seconds=300,
                code_suggestion="""concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true""",
            ))
        
        # Parallelization analysis
        parallel_candidates = self._find_parallelizable_jobs(jobs)
        if len(parallel_candidates) > 1:
            optimizations.append(Optimization(
                type=OptimizationType.PARALLEL,
                title="Parallelize independent jobs",
                description=f"Jobs {parallel_candidates} have no dependencies and can run in parallel.",
                impact=ImpactLevel.HIGH,
                confidence=0.85,
                estimated_savings_seconds=180,
                affected_jobs=parallel_candidates,
            ))
        
        # Matrix analysis for tests
        if self._could_use_matrix(jobs):
            optimizations.append(Optimization(
                type=OptimizationType.MATRIX,
                title="Use strategy.matrix for tests",
                description="Multiple tests detected that could run in parallel with matrix.",
                impact=ImpactLevel.HIGH,
                confidence=0.80,
                estimated_savings_seconds=240,
                code_suggestion=self._generate_matrix_suggestion(),
            ))
        
        return optimizations
    
    def analyze_run_history(self, runs: list[PipelineRun]) -> dict:
        """Analyze run history to identify patterns."""
        if not runs:
            return {"patterns": [], "statistics": {}}
        
        # Basic statistics
        durations = [r.duration_seconds for r in runs]
        success_count = sum(1 for r in runs if r.conclusion == "success")
        
        statistics = {
            "total_runs": len(runs),
            "success_rate": success_count / len(runs),
            "avg_duration_seconds": sum(durations) / len(durations),
            "min_duration_seconds": min(durations),
            "max_duration_seconds": max(durations),
            "duration_variance": self._calculate_variance(durations),
        }
        
        # Detect patterns
        patterns = []
        
        # Pattern: High duration variability
        if statistics["duration_variance"] > 3600:  # More than 1 hour variance
            patterns.append({
                "type": "high_variance",
                "description": "High duration variability - possible cache or resource issues",
                "recommendation": "Review cache configuration and consider more powerful runners",
            })
        
        # Pattern: High failure rate
        if statistics["success_rate"] < 0.8:
            patterns.append({
                "type": "high_failure_rate",
                "description": f"Low success rate ({statistics['success_rate']*100:.1f}%)",
                "recommendation": "Review flaky tests and retry configuration",
            })
        
        # Pattern: Slow pipelines
        if statistics["avg_duration_seconds"] > 600:  # More than 10 minutes
            patterns.append({
                "type": "slow_pipeline",
                "description": "Slow average pipeline duration",
                "recommendation": "Apply caching and parallelization optimizations",
            })
        
        return {
            "patterns": patterns,
            "statistics": statistics,
        }
    
    def _has_cache_action(self, config: dict) -> bool:
        """Check if workflow uses actions/cache."""
        config_str = json.dumps(config).lower()
        return "actions/cache" in config_str or "cache:" in config_str
    
    def _find_parallelizable_jobs(self, jobs: dict) -> list[str]:
        """Find jobs that can run in parallel."""
        no_deps = []
        for name, job_config in jobs.items():
            if "needs" not in job_config:
                no_deps.append(name)
        return no_deps
    
    def _could_use_matrix(self, jobs: dict) -> bool:
        """Determine if workflow could benefit from matrix."""
        for job_config in jobs.values():
            steps = job_config.get("steps", [])
            for step in steps:
                run_cmd = step.get("run", "")
                if any(test in run_cmd for test in ["pytest", "jest", "go test", "npm test"]):
                    if "strategy" not in job_config:
                        return True
        return False
    
    def _generate_cache_suggestion(self, config: dict) -> str:
        """Generate cache code suggestion."""
        # Detect project type
        config_str = json.dumps(config)
        
        if "pip" in config_str or "python" in config_str:
            return """- name: Cache pip dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-"""
        
        if "npm" in config_str or "node" in config_str:
            return """- name: Cache node modules
  uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-"""
        
        return """- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cache
      .cache
    key: ${{ runner.os }}-deps-${{ github.sha }}
    restore-keys: |
      ${{ runner.os }}-deps-"""
    
    def _generate_matrix_suggestion(self) -> str:
        """Generate matrix code suggestion."""
        return """strategy:
  matrix:
    test-group: [unit, integration, e2e]
  fail-fast: false
steps:
  - name: Run Tests
    run: pytest -m "${{ matrix.test-group }}" """
    
    def _calculate_variance(self, values: list[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def generate_report(
        self, 
        optimizations: list[Optimization],
        history_analysis: dict
    ) -> dict:
        """Generate complete analysis report."""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_optimizations": len(optimizations),
                "high_impact_count": sum(1 for o in optimizations if o.impact == ImpactLevel.HIGH),
                "estimated_total_savings_minutes": sum(o.estimated_savings_seconds for o in optimizations) / 60,
            },
            "optimizations": [o.to_dict() for o in optimizations],
            "history_analysis": history_analysis,
            "recommendations": self._generate_recommendations(optimizations),
        }
    
    def _generate_recommendations(self, optimizations: list[Optimization]) -> list[str]:
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Sort by impact and confidence
        sorted_opts = sorted(
            optimizations,
            key=lambda o: (o.impact.value, o.confidence),
            reverse=True
        )
        
        for i, opt in enumerate(sorted_opts[:5], 1):
            recommendations.append(
                f"{i}. {opt.title} (Estimated savings: {opt.estimated_savings_seconds/60:.1f} min)"
            )
        
        return recommendations


# Usage example
if __name__ == "__main__":
    import yaml
    
    # Sample workflow to analyze
    sample_workflow = """
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff && ruff check .
  
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest
    """
    
    config = yaml.safe_load(sample_workflow)
    
    analyzer = PipelineAnalyzer()
    optimizations = analyzer.analyze_workflow_config(config)
    
    print("🔍 Pipeline Analysis")
    print("=" * 50)
    
    for opt in optimizations:
        print(f"\n📌 {opt.title}")
        print(f"   Impact: {opt.impact.value.upper()}")
        print(f"   Confidence: {opt.confidence*100:.0f}%")
        print(f"   Estimated savings: {opt.estimated_savings_seconds/60:.1f} min")
        print(f"   {opt.description}")
