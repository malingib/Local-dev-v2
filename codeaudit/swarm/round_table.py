"""
Round Table - structured agent discussions.
"""
import asyncio
from typing import Dict, List, Any, Optional
from .consensus import ConsensusEngine, ConsensusMode

class RoundTable:
    def __init__(self, coordinator: Any):
        self.coordinator = coordinator
        self.engine = ConsensusEngine(ConsensusMode.SUPERMAJORITY)

    async def conduct_discussion(self, topic: str, question: str, agents: List[str]) -> Dict[str, Any]:
        """
        Conduct a 3-round discussion among agents.
        """
        await self.coordinator.message_bus.broadcast(
            "SYSTEM",
            f"Round Table Discussion started: {topic}\nQuestion: {question}",
            "CONSENSUS_REQUEST"
        )

        positions = {}

        # Round 1: Initial Opinions
        for agent_id in agents:
            agent = self.coordinator._agents.get(agent_id)
            if agent:
                opinion = await agent.think(f"Round Table: {topic}. Question: {question}")
                positions[agent_id] = opinion
                await self.coordinator.message_bus.broadcast(agent_id, opinion, "AGENT_DEBATE")

        # Round 2: Response to others
        await self.coordinator.message_bus.broadcast("SYSTEM", "Round 2: Agents reviewing peer opinions...", "SYSTEM_EVENT")
        all_opinions = "\n".join([f"{aid}: {op}" for aid, op in positions.items()])

        for agent_id in agents:
            agent = self.coordinator._agents.get(agent_id)
            if agent:
                response = await agent.think(f"Round Table: {topic}.\nPeer Opinions:\n{all_opinions}\n\nRefine your position based on these insights.")
                await self.coordinator.message_bus.broadcast(agent_id, response, "AGENT_DEBATE")

        # Round 3: Final Position and Vote
        votes = {}
        for agent_id in agents:
            # For demo purposes, we'll simulate a vote based on 'yes' in opinion
            opinion = positions.get(agent_id, "").lower()
            votes[agent_id] = "yes" in opinion or "agree" in opinion or "approve" in opinion

        result = self.engine.check_consensus(votes, topic=topic)

        summary = {
            "topic": topic,
            "question": question,
            "consensus": result,
            "positions": positions,
            "votes": votes
        }

        await self.coordinator.message_bus.broadcast(
            "SYSTEM",
            f"Round Table Reached Consensus: {result['reached']} (Score: {result['score']:.2f})",
            "CONSENSUS_REACHED"
        )

        return summary
