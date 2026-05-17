"""
Consensus Engine - voting and agreement mechanisms.
"""
from typing import Dict, List, Any, Optional
from enum import Enum

class ConsensusMode(Enum):
    SIMPLE = "simple"
    SUPERMAJORITY = "supermajority"
    UNANIMOUS = "unanimous"
    EXPERTISE_WEIGHTED = "expertise_weighted"

class ConsensusEngine:
    def __init__(self, mode: ConsensusMode = ConsensusMode.SUPERMAJORITY):
        self.mode = mode

    def check_consensus(self, votes: Dict[str, bool], topic: Optional[str] = None, expertise: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Check if consensus has been reached.

        Args:
            votes: Map of agent_id -> bool
            topic: The topic being voted on
            expertise: Map of agent_id -> {topic_category -> weight}

        Returns:
            Dict with 'reached', 'score', 'agreements', 'disagreements'
        """
        if not votes:
            return {"reached": False, "score": 0, "agreements": 0, "disagreements": 0}

        agree_count = sum(1 for v in votes.values() if v)
        total = len(votes)

        if self.mode == ConsensusMode.EXPERTISE_WEIGHTED and expertise and topic:
            weighted_agree = 0.0
            total_weight = 0.0
            for agent_id, vote in votes.items():
                weight = expertise.get(agent_id, {}).get(topic, 1.0)
                total_weight += weight
                if vote:
                    weighted_agree += weight
            score = weighted_agree / total_weight if total_weight > 0 else 0
        else:
            score = agree_count / total

        thresholds = {
            ConsensusMode.SIMPLE: 0.5,
            ConsensusMode.SUPERMAJORITY: 0.67,
            ConsensusMode.UNANIMOUS: 1.0,
            ConsensusMode.EXPERTISE_WEIGHTED: 0.67
        }

        threshold = thresholds.get(self.mode, 0.67)
        reached = score >= threshold

        return {
            "reached": reached,
            "score": score,
            "threshold": threshold,
            "agreements": agree_count,
            "disagreements": total - agree_count
        }
