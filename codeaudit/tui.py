"""
CodeAudit TUI - Terminal User Interface mirroring OpenCode CLI experience.
Built with Textual.
"""
import asyncio
import sys
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Input, RichLog, ListItem, ListView
from textual.binding import Binding

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from swarm import SwarmCoordinator, SwarmConfig
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from codeaudit.swarm import SwarmCoordinator, SwarmConfig

class SwarmActivity(RichLog):
    """Custom log for swarm messages."""
    pass

class CodeAuditTUI(App):
    """A Textual app for CodeAudit."""

    CSS = """
    Screen {
        background: #0f172a;
    }
    #main-container {
        height: 1fr;
    }
    #sidebar {
        width: 30;
        background: #1e293b;
        border-right: solid #334155;
    }
    #activity-feed {
        height: 1fr;
        border: double #334155;
        background: #020617;
    }
    #input-area {
        height: 3;
        dock: bottom;
    }
    .agent-item {
        padding: 1;
        border-bottom: thin #334155;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("s", "start_swarm", "Start Swarm", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.coordinator = SwarmCoordinator(SwarmConfig())
        self.coordinator.message_bus.subscribe(self.on_swarm_message)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Static(" [bold blue]AGENTS[/] ", classes="header")
                    self.agent_list = ListView()
                    yield self.agent_list
                with Vertical():
                    yield Static(" [bold yellow]SWARM ACTIVITY[/] ", classes="header")
                    self.activity_log = SwarmActivity(id="activity-feed", wrap=True, highlight=True, markup=True)
                    yield self.activity_log
        yield Input(placeholder="Ask the Swarm anything...", id="user-input")
        yield Footer()

    async def on_mount(self) -> None:
        self.activity_log.write("[bold green]Welcome to CodeAudit TUI[/]")
        self.activity_log.write("Type a task in the box below to start the swarm.")
        await self.refresh_agents()

    async def refresh_agents(self):
        self.agent_list.clear()
        for agent_id, agent in self.coordinator._agents.items():
            self.agent_list.append(ListItem(Static(f" [cyan]●[/] {agent.config.name}")))

    async def on_swarm_message(self, msg: dict):
        agent = msg.get("agent", "SYSTEM")
        content = msg.get("message", "")
        msg_type = msg.get("type", "AGENT_MESSAGE")

        color = "green" if agent == "SYSTEM" else "blue"
        if msg_type == "TASK_FAILED": color = "red"
        if msg_type == "TASK_COMPLETED": color = "bright_green"

        self.call_from_thread(
            self.activity_log.write,
            f"[[bold {color}]{agent}[/]] {content}"
        )

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value:
            task_desc = event.value
            self.activity_log.write(f"[bold magenta]USER:[/] {task_desc}")
            await self.coordinator.submit_task(task_desc)
            self.query_one("#user-input", Input).value = ""

    async def action_start_swarm(self) -> None:
        self.activity_log.write("[bold yellow]Starting Swarm...[/]")
        await self.coordinator.start()

    async def action_refresh(self) -> None:
        await self.refresh_agents()

if __name__ == "__main__":
    app = CodeAuditTUI()
    app.run()
