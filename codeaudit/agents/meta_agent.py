"""
Meta Agent - analyzes audit patterns and suggests improvements.
Runs after multiple sessions to improve the system itself.
"""
import json
from typing import List, Dict, Any, Optional
from backend.models import Session, FindingStatus
from backend.session_store import get_store
from backend.preferences import get_prefs_store
from backend.llm_router import llm_json


class MetaAgent:
    """Agent for self-improvement and system optimization."""
    
    def __init__(self):
        self.store = get_store()
        self.prefs = get_prefs_store()
    
    async def analyze_sessions(self, min_sessions: int = 5) -> Dict[str, Any]:
        """
        Analyze completed sessions to find improvement opportunities.
        
        Args:
            min_sessions: Minimum number of sessions needed for analysis
        
        Returns:
            Analysis results with recommendations
        """
        sessions = await self.store.list_all()
        
        if len(sessions) < min_sessions:
            return {
                "can_analyze": False,
                "reason": f"Need at least {min_sessions} sessions for analysis, have {len(sessions)}",
            }
        
        # Gather statistics
        stats = self._gather_statistics(sessions)
        
        # Analyze patterns
        patterns = self._analyze_patterns(sessions)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(stats, patterns)
        
        return {
            "can_analyze": True,
            "stats": stats,
            "patterns": patterns,
            "recommendations": recommendations,
        }
    
    def _gather_statistics(self, sessions: List[Session]) -> Dict[str, Any]:
        """Gather statistics from sessions."""
        total_findings = 0
        findings_by_status = {}
        findings_by_type = {}
        escalated_count = 0
        stuck_findings = []
        
        for session in sessions:
            total_findings += len(session.findings)
            
            for finding in session.findings:
                # Status counts
                status = finding.status.value if hasattr(finding.status, 'value') else str(finding.status)
                findings_by_status[status] = findings_by_status.get(status, 0) + 1
                
                # Type counts
                ftype = finding.type.value if hasattr(finding.type, 'value') else str(finding.type)
                findings_by_type[ftype] = findings_by_type.get(ftype, 0) + 1
                
                # Escalated findings
                if finding.status == FindingStatus.ESCALATED:
                    escalated_count += 1
                    stuck_findings.append({
                        "title": finding.title,
                        "type": ftype,
                        "experiments_count": len(finding.experiments),
                    })
        
        return {
            "total_sessions": len(sessions),
            "total_findings": total_findings,
            "findings_by_status": findings_by_status,
            "findings_by_type": findings_by_type,
            "escalated_count": escalated_count,
            "escalation_rate": escalated_count / total_findings if total_findings > 0 else 0,
        }
    
    def _analyze_patterns(self, sessions: List[Session]) -> Dict[str, Any]:
        """Analyze patterns in findings and rejections."""
        # Common rejection reasons
        rejection_stats = self.prefs.get_stats()
        
        # Agent performance
        agent_findings = {}
        agent_success = {}
        
        for session in sessions:
            for finding in session.findings:
                agent = finding.agent.value if hasattr(finding.agent, 'value') else str(finding.agent)
                
                if agent not in agent_findings:
                    agent_findings[agent] = 0
                    agent_success[agent] = 0
                
                agent_findings[agent] += 1
                
                # Count as success if applied or approved
                if finding.status in (FindingStatus.APPLIED, FindingStatus.APPROVED):
                    agent_success[agent] += 1
        
        agent_performance = {
            agent: {
                "findings": agent_findings[agent],
                "successes": agent_success[agent],
                "success_rate": agent_success[agent] / agent_findings[agent] if agent_findings[agent] > 0 else 0,
            }
            for agent in agent_findings
        }
        
        return {
            "rejection_stats": rejection_stats,
            "agent_performance": agent_performance,
        }
    
    async def _generate_recommendations(self, stats: Dict, patterns: Dict) -> List[Dict]:
        """Generate improvement recommendations using LLM."""
        prompt = f"""Based on the following audit system statistics, suggest improvements to the prompts and detection patterns.

STATISTICS:
- Total sessions: {stats['total_sessions']}
- Total findings: {stats['total_findings']}
- Escalation rate: {stats['escalation_rate']:.1%}
- Findings by status: {json.dumps(stats['findings_by_status'], indent=2)}
- Findings by type: {json.dumps(stats['findings_by_type'], indent=2)}

REJECTION STATS:
{json.dumps(patterns['rejection_stats'], indent=2)}

AGENT PERFORMANCE:
{json.dumps(patterns['agent_performance'], indent=2)}

Generate 3-5 specific recommendations to improve the system.
Each recommendation should include:
1. What to change
2. Why it will help
3. Priority (high/medium/low)

Return as JSON array:
[{{
  "category": "prompts|patterns|agents|workflow",
  "target": "which agent or component",
  "recommendation": "what to change",
  "rationale": "why this helps",
  "priority": "high|medium|low",
  "estimated_impact": "description of expected improvement"
}}]"""
        
        try:
            result = await llm_json(prompt, model="gemini-flash")
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            return [{
                "category": "system",
                "target": "meta_agent",
                "recommendation": "Failed to generate recommendations",
                "rationale": str(e),
                "priority": "low",
                "estimated_impact": "None - analysis failed"
            }]
    
    async def suggest_prompt_improvement(self, agent_type: str, current_prompt: str,
                                         failure_examples: List[str]) -> str:
        """
        Suggest an improved prompt for an agent.
        
        Args:
            agent_type: Type of agent
            current_prompt: Current prompt text
            failure_examples: Examples where the prompt failed
        
        Returns:
            Suggested improved prompt
        """
        prompt = f"""Improve this {agent_type} agent prompt based on failure examples.

CURRENT PROMPT:
{current_prompt}

FAILURE EXAMPLES:
{chr(10).join(f"- {ex}" for ex in failure_examples[:5])}

Provide an improved version that addresses these failures.
Keep the same structure but improve clarity, add examples, or add constraints.

Return only the improved prompt text."""
        
        try:
            from backend.llm_router import llm_call
            result = await llm_call(prompt, model="gemini-flash")
            return result.strip()
        except Exception:
            return current_prompt  # Return original on failure
    
    async def generate_agent_tuning_report(self) -> Dict[str, Any]:
        """Generate a report on how to tune agents for better performance."""
        sessions = await self.store.list_all()
        
        if len(sessions) < 3:
            return {"error": "Need at least 3 sessions for tuning report"}
        
        # Analyze each agent's findings
        agent_analysis = {}
        
        for session in sessions:
            for finding in session.findings:
                agent = finding.agent.value if hasattr(finding.agent, 'value') else str(finding.agent)
                
                if agent not in agent_analysis:
                    agent_analysis[agent] = {
                        "total": 0,
                        "applied": 0,
                        "rejected": 0,
                        "escalated": 0,
                        "common_titles": [],
                    }
                
                agent_analysis[agent]["total"] += 1
                agent_analysis[agent]["common_titles"].append(finding.title)
                
                if finding.status == FindingStatus.APPLIED:
                    agent_analysis[agent]["applied"] += 1
                elif finding.status == FindingStatus.REJECTED:
                    agent_analysis[agent]["rejected"] += 1
                elif finding.status == FindingStatus.ESCALATED:
                    agent_analysis[agent]["escalated"] += 1
        
        # Generate tuning suggestions
        tuning_suggestions = {}
        
        for agent, data in agent_analysis.items():
            success_rate = data["applied"] / data["total"] if data["total"] > 0 else 0
            rejection_rate = data["rejected"] / data["total"] if data["total"] > 0 else 0
            
            suggestions = []
            
            if success_rate < 0.5:
                suggestions.append("Consider raising confidence threshold for findings")
                suggestions.append("Add more specific detection patterns")
            
            if rejection_rate > 0.3:
                suggestions.append("Review common rejection reasons and adjust prompts")
                suggestions.append("Add more context to finding descriptions")
            
            if data["escalated"] > data["total"] * 0.2:
                suggestions.append("Hypothesis loop getting stuck - simplify patch generation")
            
            # Most common finding titles
            from collections import Counter
            common = Counter(data["common_titles"]).most_common(3)
            
            tuning_suggestions[agent] = {
                "success_rate": success_rate,
                "rejection_rate": rejection_rate,
                "escalation_rate": data["escalated"] / data["total"] if data["total"] > 0 else 0,
                "suggestions": suggestions,
                "most_common_findings": [t[0] for t in common],
            }
        
        return {
            "session_count": len(sessions),
            "agent_analysis": agent_analysis,
            "tuning_suggestions": tuning_suggestions,
        }
