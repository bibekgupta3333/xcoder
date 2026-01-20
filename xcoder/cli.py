"""
XCoder CLI Entry Point

Main command-line interface for XCoder.
"""

import typer
from rich.console import Console
from typing import Optional

from xcoder import __version__, get_logger

app = typer.Typer(
    name="xcoder",
    help="🤖 XCoder - A Local Personal Coding Agent CLI",
    add_completion=True,
)
console = Console()
logger = get_logger(__name__)


@app.command()
def version():
    """Show XCoder version"""
    console.print(f"[bold cyan]XCoder[/bold cyan] version [green]{__version__}[/green]")


@app.command()
def init(
    path: Optional[str] = typer.Option(
        ".", "--path", "-p", help="Project path to initialize"
    ),
):
    """
    Initialize XCoder in a project directory.
    
    Creates .xcoderules config and .xcoder/ directory.
    """
    console.print("[yellow]🚀 Initializing XCoder...[/yellow]")
    logger.info(f"Initializing XCoder in {path}")
    # TODO: Implement init logic
    console.print("[green]✅ XCoder initialized![/green]")


@app.command()
def ragify(
    path: Optional[str] = typer.Option(
        ".", "--path", "-p", help="Path to vectorize"
    ),
    watch: bool = typer.Option(
        False, "--watch", "-w", help="Watch for changes and auto-update"
    ),
):
    """
    Vectorize codebase for RAG.
    
    Scans code files, chunks them, and stores embeddings in vector database.
    """
    console.print("[yellow]🧠 Ragifying codebase...[/yellow]")
    logger.info(f"Ragifying path: {path}, watch: {watch}")
    # TODO: Implement ragify logic
    console.print("[green]✅ Codebase vectorized![/green]")


@app.command()
def agent(
    task: Optional[str] = typer.Argument(None, help="Task to execute"),
    role: Optional[str] = typer.Option(
        None, "--role", "-r", help="Agent role to use"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Start interactive mode"
    ),
):
    """
    Run XCoder agent for coding tasks.
    
    Can run in interactive mode or execute one-shot tasks.
    """
    console.print("[yellow]🤖 Starting XCoder agent...[/yellow]")
    logger.info(f"Agent task: {task}, role: {role}, interactive: {interactive}")
    # TODO: Implement agent logic
    console.print("[green]✅ Task completed![/green]")


@app.command()
def memory(
    action: str = typer.Argument("list", help="Action: list, search, clear, export"),
):
    """
    Manage XCoder memory.
    
    Actions: list, search, clear, export
    """
    console.print(f"[yellow]💾 Memory action: {action}[/yellow]")
    logger.info(f"Memory action: {action}")
    # TODO: Implement memory logic
    console.print("[green]✅ Memory action completed![/green]")


def main():
    """Main entry point"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
