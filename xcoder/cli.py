"""
XCoder CLI Entry Point

Main command-line interface for XCoder.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from xcoder import __version__, get_logger
from xcoder.commands import AgentCommand, InitCommand, MemoryCommand, RagifyCommand
from xcoder.utils import (
    confirm_action,
    create_progress,
    create_spinner,
    display_error,
    display_info,
    display_markdown,
    display_success,
    display_table,
    display_warning,
    print_banner,
    prompt_input,
    prompt_select,
)

# Create main app with rich help
app = typer.Typer(
    name="xcoder",
    help="🤖 XCoder - A Local Personal Coding Agent CLI powered by Ollama",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()
logger = get_logger(__name__)


# Callback for global options
@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
):
    """
    XCoder - Local Personal Coding Agent CLI

    A powerful local-first coding agent powered by Ollama that provides
    autonomous code generation, research, and task execution capabilities.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["debug"] = debug
    ctx.obj["no_color"] = no_color

    if debug:
        logger.debug("Debug mode enabled")

    if no_color:
        console.no_color = True


@app.command()
def version(
    short: bool = typer.Option(
        False,
        "--short",
        "-s",
        help="Show version number only",
    ),
):
    """Show XCoder version information"""
    if short:
        console.print(__version__)
    else:
        console.print(
            f"[bold cyan]XCoder[/bold cyan] version [bold green]{__version__}[/bold green]\n"
            f"[dim]Local Personal Coding Agent - Powered by Ollama[/dim]"
        )


@app.command()
def init(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Project path to initialize (default: current directory)",
        exists=False,
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force initialization even if already initialized",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Configuration template (python, javascript, typescript, etc.)",
    ),
):
    """
    Initialize XCoder in a project directory.

    Creates .xcoderules config and .xcoder/ directory structure.
    Detects project type and sets up appropriate defaults.

    Example:
        xcoder init
        xcoder init --path /path/to/project
        xcoder init --template python
    """
    target_path = path or Path.cwd()
    logger.info(f"Initializing XCoder in {target_path}")

    # Create and execute init command
    init_cmd = InitCommand(
        path=target_path,
        force=force,
        template=template,
    )

    success = init_cmd.execute()

    if not success:
        raise typer.Exit(code=1)


@app.command()
def ragify(
    ctx: typer.Context,
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to vectorize (default: current directory)",
        exists=True,
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch for changes and auto-update embeddings",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-vectorization of all files",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what will be vectorized without making changes",
    ),
    include: Optional[str] = typer.Option(
        None,
        "--include",
        help="File patterns to include (comma-separated glob patterns)",
    ),
    exclude: Optional[str] = typer.Option(
        None,
        "--exclude",
        help="File patterns to exclude (comma-separated glob patterns)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Embedding model to use (default: nomic-embed-text)",
    ),
):
    """
    Vectorize codebase for RAG (Retrieval-Augmented Generation).

    Scans code files, extracts chunks using AST parsing, generates embeddings
    using Ollama, and stores them in ChromaDB for semantic search.

    Supports incremental updates - only processes new or changed files.

    Example:
        xcoder ragify                          # Vectorize current directory
        xcoder ragify --dry-run                # Preview what will be processed
        xcoder ragify --force                  # Re-vectorize all files
        xcoder ragify --include "*.py"         # Only Python files
        xcoder ragify --exclude "test_*"       # Exclude test files
        xcoder ragify --model all-minilm       # Use different embedding model
        xcoder ragify --watch                  # Watch mode (coming soon)
    """
    target_path = path or Path.cwd()
    logger.info(
        f"Ragifying path: {target_path}, watch: {watch}, force: {force}, dry_run: {dry_run}"
    )

    # Parse include/exclude patterns
    include_patterns = [p.strip() for p in include.split(",")] if include else None
    exclude_patterns = [p.strip() for p in exclude.split(",")] if exclude else None

    # Create and execute ragify command
    ragify_cmd = RagifyCommand(
        path=target_path,
        watch=watch,
        force=force,
        dry_run=dry_run,
        include=include_patterns,
        exclude=exclude_patterns,
        model=model,
    )

    success = ragify_cmd.execute()

    if not success:
        raise typer.Exit(code=1)


@app.command()
def agent(
    ctx: typer.Context,
    task: Optional[str] = typer.Argument(
        None,
        help="Task to execute (omit for interactive mode)",
    ),
    role: Optional[str] = typer.Option(
        None,
        "--role",
        "-r",
        help="Agent role: general, backend, frontend, devops, testing, documentation",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Start interactive chat mode",
    ),
    context: Optional[str] = typer.Option(
        None,
        "--context",
        "-c",
        help="Additional context files (comma-separated paths)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Ollama model to use (default: codellama:7b)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Project path (default: current directory)",
    ),
):
    """
    Run XCoder agent for autonomous coding tasks.

    Can run in interactive mode with conversation history or execute one-shot tasks.
    Uses RAG to retrieve relevant code context from your vectorized codebase.

    Slash Commands (Interactive Mode):
        /help     - Show available commands
        /exit     - Exit interactive mode
        /clear    - Clear conversation history
        /save     - Save current conversation
        /context  - Show current context
        /role     - Change agent role
        /model    - Change LLM model

    Example:
        xcoder agent "Add error handling to auth service"
        xcoder agent --interactive --role backend
        xcoder agent "Refactor user model" --context models/user.py
        xcoder agent -i --model deepseek-coder:6.7b
    """
    logger.info(f"Agent task: {task}, role: {role}, interactive: {interactive}")

    # Parse context files if provided
    context_files = None
    if context:
        context_files = [Path(p.strip()) for p in context.split(",")]

    # Create and execute agent command
    from xcoder.commands import AgentCommand

    agent_cmd = AgentCommand(
        task=task,
        role=role,
        model=model,
        context_files=context_files,
        interactive=interactive,
        path=path or Path.cwd(),
    )

    success = agent_cmd.execute()

    if not success:
        raise typer.Exit(code=1)


@app.command(name="memory")
def memory_cmd(
    ctx: typer.Context,
    action: str = typer.Argument(
        "list",
        help="Action: list, search, clear, export, stats, delete",
    ),
    query: Optional[str] = typer.Option(
        None,
        "--query",
        "-q",
        help="Search query (for search action)",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Number of results to show",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (for export action)",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format: json, markdown, csv",
    ),
    role: Optional[str] = typer.Option(
        None,
        "--role",
        "-r",
        help="Filter by agent role",
    ),
    conv_id: Optional[str] = typer.Option(
        None,
        "--conv-id",
        help="Specific conversation ID (for delete/export)",
    ),
    path: Optional[Path] = typer.Option(
        None,
        "--path",
        "-p",
        help="Project path (default: current directory)",
    ),
):
    """
    Manage XCoder memory and conversation history.

    Actions:
    - list    : Show recent conversations
    - search  : Search memory by keyword
    - clear   : Clear all memory (requires confirmation)
    - export  : Export memory to file (JSON, Markdown, or CSV)
    - stats   : Show memory statistics
    - delete  : Delete a specific conversation

    Example:
        xcoder memory list --limit 20
        xcoder memory search --query "authentication"
        xcoder memory export --output backup.json --format json
        xcoder memory export --output docs.md --format markdown
        xcoder memory stats
        xcoder memory delete --conv-id abc123
        xcoder memory clear
    """
    logger.info(f"Memory action: {action}, query: {query}")

    # Create and execute memory command
    from xcoder.commands import MemoryCommand

    memory_cmd_obj = MemoryCommand(
        action=action,
        query=query,
        output=output,
        format=format,
        role=role,
        limit=limit,
        conv_id=conv_id,
        path=path or Path.cwd(),
    )

    success = memory_cmd_obj.execute()

    if not success:
        raise typer.Exit(code=1)


@app.command()
def config(
    ctx: typer.Context,
    action: str = typer.Argument(
        "show",
        help="Action: show, set, reset",
    ),
    key: Optional[str] = typer.Option(
        None,
        "--key",
        "-k",
        help="Configuration key",
    ),
    value: Optional[str] = typer.Option(
        None,
        "--value",
        "-v",
        help="Configuration value",
    ),
):
    """
    Manage XCoder configuration.

    Actions:
    - show: Display current configuration
    - set: Set a configuration value
    - reset: Reset to defaults

    Example:
        xcoder config show
        xcoder config set --key model --value codellama
        xcoder config reset
    """
    # TODO: Implement config management
    display_info(f"Configuration action: {action}")


def main():
    """Main entry point with enhanced error handling"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        display_error("An unexpected error occurred", exception=e)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
    main()
