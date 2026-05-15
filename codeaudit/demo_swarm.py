#!/usr/bin/env python3
"""
Demo script for the CodeAudit Agent Swarm.

This demonstrates how the swarm works with a simple example.
"""
import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from swarm import SwarmCoordinator, SwarmConfig


async def main():
    print("=" * 60)
    print("CodeAudit Agent Swarm Demo")
    print("=" * 60)
    
    # Initialize swarm
    print("\n[1] Initializing swarm...")
    config = SwarmConfig(
        persist_dir="./demo_swarm_data",
        enable_self_modification=True,
        default_model="gemini-flash"
    )
    
    coordinator = SwarmCoordinator(config)
    
    # Show available agents
    print(f"\n[2] Available agents ({len(coordinator._agents)}):")
    for agent_id, agent in coordinator._agents.items():
        print(f"    - {agent.config.name}: {agent.config.role[:50]}...")
    
    # Show available models
    print(f"\n[3] Available models:")
    for model in coordinator.get_available_models():
        print(f"    - {model}")
    
    # Start swarm
    print("\n[4] Starting swarm...")
    await coordinator.start()
    
    # Get initial status
    status = coordinator.get_status()
    print(f"\n[5] Swarm status:")
    print(f"    Running: {status['running']}")
    print(f"    Agents: {len(status['agents'])}")
    print(f"    Pending tasks: {status['pending_tasks']}")
    
    # Submit a sample task
    print("\n[6] Submitting sample task...")
    task_id = await coordinator.submit_task(
        description="Review authentication module for security issues",
        task_type="security_audit",
        requirements=["Check for SQL injection", "Verify input validation", "Review password handling"],
        priority="high"
    )
    print(f"    Task ID: {task_id}")
    
    # Wait a bit for agents to process
    print("\n[7] Waiting for agents to process (3 seconds)...")
    await asyncio.sleep(3)
    
    # Check activity
    print("\n[8] Recent activity:")
    activity = await coordinator.get_recent_activity(limit=10)
    for item in activity:
        print(f"    [{item['agent']}] {item['message'][:60]}...")
    
    # Show context summary
    print(f"\n[9] Shared context summary:")
    summary = coordinator._context.get_summary()
    for key, value in summary.items():
        print(f"    {key}: {value}")
    
    # Demonstrate model switching
    print("\n[10] Switching Coder agent to Groq...")
    coordinator.switch_agent_model("coder", "groq/llama-3.3-70b")
    agent_status = coordinator.get_agent_status("coder")
    print(f"    Coder now using: {agent_status['model']}")
    
    # Submit another task
    print("\n[11] Submitting UI task...")
    task_id2 = await coordinator.submit_task(
        description="Design login form component",
        task_type="ui_design",
        requirements=["Responsive", "Accessible", "Dark mode support"],
        priority="normal"
    )
    print(f"    Task ID: {task_id2}")
    
    # Wait again
    print("\n[12] Waiting for processing (3 seconds)...")
    await asyncio.sleep(3)
    
    # Final status
    print("\n[13] Final swarm status:")
    final_status = coordinator.get_status()
    print(f"    Running: {final_status['running']}")
    print(f"    Pending tasks: {final_status['pending_tasks']}")
    
    # Show agent statuses
    print(f"\n[14] Agent statuses:")
    for agent_id in coordinator._agents:
        status = coordinator.get_agent_status(agent_id)
        print(f"    {status['name']}: running={status['running']}, model={status['model']}")
    
    # Stop swarm
    print("\n[15] Stopping swarm...")
    await coordinator.stop()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("\nThe swarm demonstrated:")
    print("  ✓ Multi-agent initialization")
    print("  ✓ Task submission and distribution")
    print("  ✓ Message-based communication")
    print("  ✓ Shared context/memory")
    print("  ✓ Model switching per-agent")
    print("  ✓ Activity logging")
    print("\nTo see the full system, run: python start.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
