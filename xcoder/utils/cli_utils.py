"""
CLI Utility Functions

Provides rich console output, spinners, progress bars, and interactive prompts.
"""

from typing import Any, List, Optional

import questionary
from questionary import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.syntax import Syntax
from rich.table import Table

# Console instance
console = Console()

# Custom questionary style
custom_style = Style(
    [
        ("qmark", "fg:#673ab7 bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", "fg:#673ab7 bold"),
        ("highlighted", "fg:#673ab7 bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
    ]
)


def create_spinner(text: str = "Processing..."):
    """
    Create a rich progress spinner.

    Args:
        text: Text to display with spinner

    Returns:
        Progress context manager

    Example:
        with create_spinner("Loading...") as progress:
            task = progress.add_task("[cyan]Working...", total=None)
            # Do work
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def create_progress(description: str = "Processing..."):
    """
    Create a rich progress bar.

    Args:
        description: Description of the task

    Returns:
        Progress context manager

    Example:
        with create_progress("Vectorizing files") as progress:
            task = progress.add_task("[cyan]Processing", total=100)
            for i in range(100):
                progress.update(task, advance=1)
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def confirm_action(
    message: str,
    default: bool = False,
    style: Style = custom_style,
) -> bool:
    """
    Prompt user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter
        style: Questionary style

    Returns:
        True if user confirmed, False otherwise

    Example:
        if confirm_action("Delete all data?"):
            delete_data()
    """
    return questionary.confirm(
        message,
        default=default,
        style=style,
    ).ask()


def prompt_input(
    message: str,
    default: Optional[str] = None,
    validate: Optional[callable] = None,
    style: Style = custom_style,
) -> str:
    """
    Prompt user for text input.

    Args:
        message: Prompt message
        default: Default value
        validate: Validation function
        style: Questionary style

    Returns:
        User input

    Example:
        name = prompt_input("Enter project name:", default="my-project")
    """
    return questionary.text(
        message,
        default=default or "",
        validate=validate,
        style=style,
    ).ask()


def prompt_select(
    message: str,
    choices: List[str],
    default: Optional[str] = None,
    style: Style = custom_style,
) -> str:
    """
    Prompt user to select from a list.

    Args:
        message: Prompt message
        choices: List of choices
        default: Default selection
        style: Questionary style

    Returns:
        Selected choice

    Example:
        role = prompt_select(
            "Select agent role:",
            choices=["Backend", "Frontend", "DevOps"]
        )
    """
    return questionary.select(
        message,
        choices=choices,
        default=default,
        style=style,
    ).ask()


def display_error(message: str, exception: Optional[Exception] = None):
    """
    Display error message with rich formatting.

    Args:
        message: Error message
        exception: Optional exception to display

    Example:
        display_error("Failed to connect to database", exception=e)
    """
    if exception:
        console.print(
            Panel(
                f"[bold red]❌ Error:[/bold red] {message}\n\n"
                f"[dim]{type(exception).__name__}: {str(exception)}[/dim]",
                border_style="red",
                title="Error",
            )
        )
    else:
        console.print(f"[bold red]❌ {message}[/bold red]")


def display_success(message: str, details: Optional[str] = None):
    """
    Display success message with rich formatting.

    Args:
        message: Success message
        details: Optional details

    Example:
        display_success("Project initialized!", details="Created .xcoder/ directory")
    """
    if details:
        console.print(
            Panel(
                f"[bold green]✅ {message}[/bold green]\n\n[dim]{details}[/dim]",
                border_style="green",
                title="Success",
            )
        )
    else:
        console.print(f"[bold green]✅ {message}[/bold green]")


def display_warning(message: str):
    """
    Display warning message with rich formatting.

    Args:
        message: Warning message

    Example:
        display_warning("This action cannot be undone!")
    """
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


def display_info(message: str):
    """
    Display info message with rich formatting.

    Args:
        message: Info message

    Example:
        display_info("Scanning 1,234 files...")
    """
    console.print(f"[bold cyan]ℹ️  {message}[/bold cyan]")


def display_code(code: str, language: str = "python", theme: str = "monokai"):
    """
    Display syntax-highlighted code.

    Args:
        code: Code to display
        language: Programming language
        theme: Syntax theme

    Example:
        display_code('def hello():\n    print("Hi")', language="python")
    """
    syntax = Syntax(code, language, theme=theme, line_numbers=True)
    console.print(syntax)


def display_markdown(text: str):
    """
    Display markdown-formatted text.

    Args:
        text: Markdown text

    Example:
        display_markdown("# Hello\\n\\nThis is **bold**")
    """
    md = Markdown(text)
    console.print(md)


def display_table(title: str, columns: List[str], rows: List[List[Any]]):
    """
    Display a formatted table.

    Args:
        title: Table title
        columns: Column headers
        rows: Table rows

    Example:
        display_table(
            "Files",
            ["Name", "Size", "Type"],
            [["app.py", "1.2 KB", "Python"], ["main.js", "3.4 KB", "JavaScript"]]
        )
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    for column in columns:
        table.add_column(column)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def clear_console():
    """Clear the console."""
    console.clear()


def print_banner():
    """Print XCoder ASCII banner."""
    banner = r"""
[bold cyan]
 __   __  _____   ___   ______   _______   ______ 
 \ \ / / / ____| / _ \ |  _ \ \ / /  __ \ |  ____|
  \ V / | |     | | | || | | \ V /| |  | || |     
   > <  | |     | | | || | | |> < | |  | || |     
  / . \ | |____ | |_| || |_| / . \| |__| || |____ 
 /_/ \_\ \_____| \___/ |____/_/ \_\_____/ |______|
                                                   
[/bold cyan][dim]Local Personal Coding Agent - Powered by Ollama[/dim]
"""
    console.print(banner)
    console.print(banner)
