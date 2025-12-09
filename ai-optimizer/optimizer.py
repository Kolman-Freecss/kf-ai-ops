"""
AI Optimizer - Intelligently applies optimizations to pipelines.
Integrates with OpenAI for advanced analysis and code generation.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional
import yaml

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from analyzer import PipelineAnalyzer, Optimization, OptimizationType, ImpactLevel


@dataclass
class OptimizationResult:
    """Result of applying an optimization."""
    success: bool
    optimization: Optimization
    original_config: dict
    optimized_config: dict
    diff: str
    message: str


class AIOptimizer:
    """
    AI-powered pipeline optimizer.
    
    Combines rule-based analysis with LLM capabilities
    to generate more sophisticated optimizations.
    """
    
    SYSTEM_PROMPT = """You are a CI/CD and DevOps expert. Your task is to analyze 
GitHub Actions workflows and suggest specific, practical optimizations.

Focus on:
1. Reducing execution time
2. Improving cache usage
3. Parallelizing when possible
4. Eliminating redundancies
5. Improving reliability

Always respond in structured JSON format."""

    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.analyzer = PipelineAnalyzer(github_token)
        
        if HAS_OPENAI and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.ai_enabled = True
        else:
            self.client = None
            self.ai_enabled = False
    
    def optimize_workflow(
        self, 
        workflow_path: str,
        auto_apply: bool = False,
        confidence_threshold: float = 0.8
    ) -> list[OptimizationResult]:
        """
        Optimize a complete workflow.
        
        Args:
            workflow_path: Path to workflow file
            auto_apply: Whether to apply changes automatically
            confidence_threshold: Minimum confidence threshold to apply
        
        Returns:
            List of optimization results
        """
        # Read workflow
        with open(workflow_path) as f:
            original_content = f.read()
            config = yaml.safe_load(original_content)
        
        # Rule-based analysis
        rule_optimizations = self.analyzer.analyze_workflow_config(config)
        
        # AI analysis (if available)
        if self.ai_enabled:
            ai_optimizations = self._analyze_with_ai(config)
            all_optimizations = self._merge_optimizations(rule_optimizations, ai_optimizations)
        else:
            all_optimizations = rule_optimizations
        
        # Apply optimizations
        results = []
        optimized_config = config.copy()
        
        for opt in all_optimizations:
            if opt.confidence >= confidence_threshold:
                result = self._apply_optimization(optimized_config, opt)
                results.append(result)
                
                if result.success:
                    optimized_config = result.optimized_config
        
        # Save if auto_apply is enabled
        if auto_apply and results:
            self._save_workflow(workflow_path, optimized_config)
        
        return results
    
    def _analyze_with_ai(self, config: dict) -> list[Optimization]:
        """Analyze workflow using OpenAI."""
        if not self.ai_enabled:
            return []
        
        prompt = f"""Analyze this GitHub Actions workflow and suggest optimizations:

```yaml
{yaml.dump(config, default_flow_style=False)}
```

Respond with a JSON array of optimizations, each with:
- type: optimization type (cache, parallel, skip_redundant, etc.)
- title: brief title
- description: detailed description
- confidence: confidence 0-1
- estimated_savings_seconds: estimated savings in seconds
- code_suggestion: suggested YAML code (optional)

Only include high-confidence, high-value optimizations."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=2000,
            )
            
            result = json.loads(response.choices[0].message.content)
            optimizations = []
            
            for opt_data in result.get("optimizations", []):
                try:
                    opt_type = OptimizationType(opt_data.get("type", "cache"))
                except ValueError:
                    opt_type = OptimizationType.CACHE
                
                optimizations.append(Optimization(
                    type=opt_type,
                    title=opt_data.get("title", "AI Suggestion"),
                    description=opt_data.get("description", ""),
                    impact=ImpactLevel.MEDIUM,
                    confidence=opt_data.get("confidence", 0.7),
                    estimated_savings_seconds=opt_data.get("estimated_savings_seconds", 60),
                    code_suggestion=opt_data.get("code_suggestion"),
                ))
            
            return optimizations
            
        except Exception as e:
            print(f"AI analysis error: {e}")
            return []
    
    def _merge_optimizations(
        self, 
        rule_opts: list[Optimization],
        ai_opts: list[Optimization]
    ) -> list[Optimization]:
        """Combine rule and AI optimizations, removing duplicates."""
        merged = {opt.type.value: opt for opt in rule_opts}
        
        for ai_opt in ai_opts:
            key = ai_opt.type.value
            if key in merged:
                # Increase confidence if both agree
                merged[key].confidence = min(0.99, merged[key].confidence + 0.1)
            else:
                merged[key] = ai_opt
        
        return list(merged.values())
    
    def _apply_optimization(
        self, 
        config: dict, 
        optimization: Optimization
    ) -> OptimizationResult:
        """Apply a specific optimization to config."""
        original = config.copy()
        optimized = config.copy()
        success = False
        diff = ""
        message = ""
        
        try:
            if optimization.type == OptimizationType.CACHE:
                optimized, diff = self._add_cache(optimized, optimization)
                success = True
                message = "Cache added successfully"
                
            elif optimization.type == OptimizationType.CONCURRENCY:
                optimized, diff = self._add_concurrency(optimized, optimization)
                success = True
                message = "Concurrency control added"
                
            elif optimization.type == OptimizationType.PARALLEL:
                # Requires manual review
                success = False
                message = "Parallelization requires manual review"
                diff = optimization.code_suggestion or ""
                
            elif optimization.type == OptimizationType.MATRIX:
                optimized, diff = self._add_matrix(optimized, optimization)
                success = True
                message = "Matrix strategy added"
                
            else:
                message = f"Type {optimization.type.value} not supported for auto-apply"
                
        except Exception as e:
            message = f"Error applying optimization: {e}"
        
        return OptimizationResult(
            success=success,
            optimization=optimization,
            original_config=original,
            optimized_config=optimized,
            diff=diff,
            message=message,
        )
    
    def _add_cache(self, config: dict, opt: Optimization) -> tuple[dict, str]:
        """Add cache step to workflow."""
        cache_step = {
            "name": "Cache Dependencies",
            "uses": "actions/cache@v4",
            "with": {
                "path": "~/.cache/pip\nnode_modules",
                "key": "${{ runner.os }}-deps-${{ hashFiles('**/requirements.txt', '**/package-lock.json') }}",
                "restore-keys": "${{ runner.os }}-deps-"
            }
        }
        
        # Add after checkout in each job
        for job_name, job_config in config.get("jobs", {}).items():
            steps = job_config.get("steps", [])
            
            # Find position after checkout
            insert_pos = 0
            for i, step in enumerate(steps):
                if "checkout" in str(step.get("uses", "")):
                    insert_pos = i + 1
                    break
            
            # Insert cache step
            steps.insert(insert_pos, cache_step.copy())
            job_config["steps"] = steps
        
        diff = yaml.dump(cache_step)
        return config, diff
    
    def _add_concurrency(self, config: dict, opt: Optimization) -> tuple[dict, str]:
        """Add concurrency control to workflow."""
        config["concurrency"] = {
            "group": "${{ github.workflow }}-${{ github.ref }}",
            "cancel-in-progress": True
        }
        
        diff = yaml.dump({"concurrency": config["concurrency"]})
        return config, diff
    
    def _add_matrix(self, config: dict, opt: Optimization) -> tuple[dict, str]:
        """Add matrix strategy to test jobs."""
        for job_name, job_config in config.get("jobs", {}).items():
            # Only add to jobs that look like tests
            if "test" in job_name.lower():
                job_config["strategy"] = {
                    "matrix": {
                        "test-group": ["unit", "integration"]
                    },
                    "fail-fast": False
                }
        
        diff = yaml.dump({"strategy": config.get("jobs", {}).get("test", {}).get("strategy", {})})
        return config, diff
    
    def _save_workflow(self, path: str, config: dict):
        """Save optimized workflow."""
        # Create backup
        backup_path = f"{path}.backup"
        with open(path) as f:
            original = f.read()
        with open(backup_path, "w") as f:
            f.write(original)
        
        # Save optimized
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def generate_optimization_pr_body(self, results: list[OptimizationResult]) -> str:
        """Generate PR body with optimizations."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        body = """## 🤖 AI Pipeline Optimizations

This PR contains automatic optimizations generated by AI Optimizer.

### ✅ Applied Optimizations

"""
        
        for r in successful:
            opt = r.optimization
            body += f"""#### {opt.title}
- **Type**: `{opt.type.value}`
- **Impact**: {opt.impact.value.upper()}
- **Confidence**: {opt.confidence*100:.0f}%
- **Estimated savings**: {opt.estimated_savings_seconds/60:.1f} min

{opt.description}

"""
        
        if failed:
            body += "\n### ⚠️ Require Manual Review\n\n"
            for r in failed:
                opt = r.optimization
                body += f"- **{opt.title}**: {r.message}\n"
        
        body += """
### 📊 Summary

| Metric | Value |
|--------|-------|
| Applied optimizations | """ + str(len(successful)) + """ |
| Require review | """ + str(len(failed)) + """ |
| Total estimated savings | """ + f"{sum(r.optimization.estimated_savings_seconds for r in successful)/60:.1f} min" + """ |

---
*Automatically generated by AI Pipeline Optimizer*
"""
        
        return body


# CLI for direct usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Pipeline Optimizer")
    parser.add_argument("workflow", help="Path to workflow file")
    parser.add_argument("--apply", action="store_true", help="Apply changes automatically")
    parser.add_argument("--threshold", type=float, default=0.8, help="Confidence threshold")
    
    args = parser.parse_args()
    
    optimizer = AIOptimizer()
    results = optimizer.optimize_workflow(
        args.workflow,
        auto_apply=args.apply,
        confidence_threshold=args.threshold
    )
    
    print("\n🤖 AI Optimization Results")
    print("=" * 50)
    
    for r in results:
        status = "✅" if r.success else "⚠️"
        print(f"\n{status} {r.optimization.title}")
        print(f"   {r.message}")
        if r.diff:
            print(f"   Diff:\n{r.diff}")
