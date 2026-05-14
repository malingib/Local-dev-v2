"""
Hypothesis engine - drives the debug loop for each finding.
Implements: hypothesize -> experiment -> update beliefs -> converge/stuck/escalate.
"""
import json
from typing import List, Tuple, Optional
from pathlib import Path
from backend.models import Finding, Hypothesis, Experiment, FindingStatus
from backend.llm_router import llm_json, llm_call
from backend.session_store import get_store

STUCK_THRESHOLD = 3      # experiments with < 5% confidence change = stuck
INFO_GAIN_THRESHOLD = 0.05
CONFIRM_THRESHOLD = 0.85
RULE_OUT_THRESHOLD = 0.10

class HypothesisEngine:
    def __init__(self, session_id: str, max_steps: int = 20):
        self.session_id = session_id
        self.store = get_store()
        self.max_steps = max_steps

    async def run(self, finding: Finding, project_path: str) -> Finding:
        """Run the full hypothesis loop for a finding. Returns updated finding."""
        await self.store.log_activity(
            self.session_id, "hypothesis_engine",
            f"Starting hypothesis loop for: {finding.title}"
        )
        
        # Generate initial hypotheses
        hypotheses = await self._generate_hypotheses(finding, project_path)
        finding.hypothesis_tree = hypotheses
        
        steps = 0
        low_gain_streak = 0
        
        while steps < self.max_steps:
            # Check for confirmed hypothesis
            confirmed = [h for h in finding.hypothesis_tree if h.status == "confirmed"]
            if confirmed:
                finding.status = FindingStatus.AWAITING_APPROVAL
                await self._generate_patch(finding, confirmed[0], project_path)
                break
            
            # Check for stuck condition
            if low_gain_streak >= STUCK_THRESHOLD:
                finding.status = FindingStatus.ESCALATED
                await self.store.log_activity(
                    self.session_id, "hypothesis_engine",
                    f"Stuck on {finding.title} after {steps} steps. Escalating.", "warning"
                )
                break
            
            # Select best experiment
            active = [h for h in finding.hypothesis_tree if h.status == "active"]
            if not active:
                finding.status = FindingStatus.ESCALATED
                break
            
            experiment = await self._select_experiment(active, finding, project_path)
            
            # Execute experiment
            result = await self._execute_experiment(experiment, project_path)
            experiment.result = result
            finding.experiments.append(experiment)
            
            # Update beliefs
            gain = await self._update_beliefs(finding, experiment, result)
            experiment.information_gain = gain
            
            if gain < INFO_GAIN_THRESHOLD:
                low_gain_streak += 1
            else:
                low_gain_streak = 0
            
            steps += 1
            await self.store.log_activity(
                self.session_id, "hypothesis_engine",
                f"Step {steps}: gain={gain:.2f}, active hypotheses={len(active)}"
            )
        
        if steps >= self.max_steps:
            finding.status = FindingStatus.ESCALATED
        
        return finding

    async def _generate_hypotheses(self, finding: Finding, 
                                    project_path: str) -> List[Hypothesis]:
        location_info = json.dumps(finding.location)
        
        prompt = f"""Generate 3-4 hypotheses for this code finding.

FINDING: {finding.title}
DESCRIPTION: {finding.description}
LOCATION: {location_info}
SEVERITY: {finding.severity}

Each hypothesis should be a specific, falsifiable claim about the root cause.
Order by likelihood (most likely first).

Return JSON array:
[{{
  "claim": "specific claim about what causes this issue",
  "confidence": 0.6,
  "status": "active"
}}]"""

        try:
            data = await llm_json(prompt, model="gemini-flash")
            if not isinstance(data, list):
                await self.store.log_activity(
                    self.session_id, "hypothesis_engine",
                    f"LLM returned non-list shape for hypotheses: {type(data).__name__}, falling back",
                    "warning"
                )
                raw = []
            else:
                raw = data
            return [Hypothesis(**item) for item in raw[:4]]
        except Exception as e:
            await self.store.log_activity(
                self.session_id, "hypothesis_engine",
                f"Hypothesis generation failed: {e}, using fallback", "warning"
            )
            # Fallback single hypothesis
            return [Hypothesis(
                claim=f"The issue described in the finding is present as described",
                confidence=0.5
            )]

    async def _select_experiment(self, active: List[Hypothesis], 
                                  finding: Finding, project_path: str) -> Experiment:
        hyp_summary = "\n".join([f"- {h.claim} (confidence: {h.confidence:.2f})" 
                                  for h in active])
        
        prompt = f"""Select the best experiment to maximize information gain.

FINDING: {finding.title}
LOCATION: {json.dumps(finding.location)}
PROJECT PATH: {project_path}

ACTIVE HYPOTHESES:
{hyp_summary}

Choose the cheapest experiment that would most distinguish between these hypotheses.
Prefer: read_file > grep > run_test > run_command

Return JSON:
{{
  "hypothesis_id": "id of hypothesis this tests",
  "action": "what we're doing and why",
  "tool": "read_file|grep|run_test|run_command|screenshot",
  "params": {{
    "file": "relative/path/to/file.py",
    "pattern": "optional grep pattern",
    "command": "optional command to run"
  }}
}}"""

        try:
            data = await llm_json(prompt, model="gemini-flash")
            return Experiment(
                hypothesis_id=data.get("hypothesis_id", active[0].id),
                action=data.get("action", "Read relevant file"),
                tool=data.get("tool", "read_file"),
                params=data.get("params", {})
            )
        except Exception:
            # Default to reading the file mentioned in finding
            file_path = finding.location.get("file", "")
            return Experiment(
                hypothesis_id=active[0].id,
                action=f"Read {file_path} to examine the issue",
                tool="read_file",
                params={"file": file_path}
            )

    async def _execute_experiment(self, experiment: Experiment, 
                                   project_path: str) -> str:
        path = Path(project_path)
        
        try:
            if experiment.tool == "read_file":
                file_path = experiment.params.get("file", "")
                fp = path / file_path
                if fp.exists():
                    content = fp.read_text(errors="ignore")
                    return content[:5000]  # Cap at 5KB
                return f"File not found: {file_path}"
            
            elif experiment.tool == "grep":
                import subprocess
                pattern = experiment.params.get("pattern", "")
                result = subprocess.run(
                    ["grep", "-rn", "--include=*.py", "--include=*.js", 
                     "--include=*.ts", pattern, str(path)],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout[:3000] or "No matches found"
            
            elif experiment.tool == "run_test":
                return "Test execution requires running environment (Phase 2)"
            
            else:
                return f"Tool {experiment.tool} not yet supported in Phase 1"
                
        except Exception as e:
            return f"Experiment failed: {e}"

    async def _update_beliefs(self, finding: Finding, 
                               experiment: Experiment, result: str) -> float:
        hyp_summary = "\n".join([
            f"[{h.id}] {h.claim} (confidence: {h.confidence:.2f}, status: {h.status})"
            for h in finding.hypothesis_tree
        ])
        
        prompt = f"""Update hypothesis confidence based on this experiment result.

HYPOTHESES:
{hyp_summary}

EXPERIMENT: {experiment.action}
RESULT (truncated):
{result[:2000]}

For each hypothesis, update its confidence and status.
Return JSON:
{{
  "updates": [
    {{
      "id": "hypothesis_id",
      "new_confidence": 0.85,
      "new_status": "active|confirmed|ruled_out",
      "evidence": "why this result changed confidence"
    }}
  ],
  "information_gain": 0.3
}}

Rules:
- confirmed if confidence > 0.85
- ruled_out if confidence < 0.10
- Spawn new hypotheses if result reveals unexpected information"""

        try:
            data = await llm_json(prompt, model="gemini-flash")
            
            for update in data.get("updates", []):
                for h in finding.hypothesis_tree:
                    if h.id == update.get("id"):
                        old_conf = h.confidence
                        h.confidence = float(update.get("new_confidence", h.confidence))
                        h.status = update.get("new_status", h.status)
                        if update.get("evidence"):
                            if h.confidence > old_conf:
                                h.evidence_for.append(update["evidence"])
                            else:
                                h.evidence_against.append(update["evidence"])
            
            return float(data.get("information_gain", 0.0))
            
        except Exception:
            return 0.0

    async def _generate_patch(self, finding: Finding, 
                               confirmed: Hypothesis, project_path: str) -> None:
        file_path = finding.location.get("file", "")
        fp = Path(project_path) / file_path
        
        current_code = ""
        if fp.exists():
            current_code = fp.read_text(errors="ignore")[:5000]
        
        prompt = f"""Generate a minimal patch for this confirmed issue.

FINDING: {finding.title}
ROOT CAUSE: {confirmed.claim}
FILE: {file_path}

CURRENT CODE:
{current_code}

Generate the fix. Be minimal - change only what is necessary.
Explain the change clearly.

Return JSON:
{{
  "patch_description": "plain English explanation of what changed and why",
  "changes": [
    {{
      "file": "relative/path",
      "find": "exact text to find",
      "replace": "replacement text"
    }}
  ]
}}"""

        try:
            data = await llm_json(prompt, model="gemini-flash")
            finding.patch_explanation = data.get("patch_description", "")
            finding.proposed_patch = json.dumps(data.get("changes", []))
        except Exception:
            finding.patch_explanation = f"Confirmed: {confirmed.claim}. Manual fix required."
            finding.proposed_patch = "[]"
