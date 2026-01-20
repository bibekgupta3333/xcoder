"""
Memory Command Implementation

Handles memory management operations.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from xcoder import get_logger
from xcoder.memory import MemoryManager
from xcoder.utils import (
    confirm_action,
    display_error,
    display_info,
    display_success,
    display_table,
    display_warning,
)

logger = get_logger(__name__)


class MemoryCommand:
    """Manage XCoder memory."""

    VALID_ACTIONS = ["list", "clear", "export", "search", "stats", "delete"]
    VALID_FORMATS = ["json", "markdown", "csv"]

    def __init__(
        self,
        action: str,
        query: Optional[str] = None,
        output: Optional[Path] = None,
        format: str = "json",
        role: Optional[str] = None,
        limit: Optional[int] = None,
        conv_id: Optional[str] = None,
        path: Optional[Path] = None,
    ):
        """
        Initialize MemoryCommand.

        Args:
            action: Action to perform (list, clear, export, search, stats, delete)
            query: Search query
            output: Output file path (for export)
            format: Export format (json, markdown, csv)
            role: Filter by role
            limit: Maximum results
            conv_id: Specific conversation ID
            path: Project path
        """
        self.action = action.lower()
        self.query = query
        self.output = output
        self.format = format
        self.role = role
        self.limit = limit
        self.conv_id = conv_id
        self.path = (path or Path.cwd()).resolve()

        # Validate action
        if self.action not in self.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action: {self.action}. "
                f"Must be one of: {', '.join(self.VALID_ACTIONS)}"
            )

        # Validate format
        if self.format not in self.VALID_FORMATS:
            raise ValueError(
                f"Invalid format: {self.format}. "
                f"Must be one of: {', '.join(self.VALID_FORMATS)}"
            )

        # Initialize memory manager
        xcoder_dir = self.path / ".xcoder"
        if not xcoder_dir.exists():
            raise FileNotFoundError(
                f"XCoder not initialized in {self.path}. Run 'xcoder init' first."
            )

        memory_dir = xcoder_dir / "memory"
        self.memory_manager = MemoryManager(memory_dir)

    def execute(self) -> bool:
        """
        Execute memory operation.

        Returns:
            True if successful
        """
        try:
            if self.action == "list":
                return self._list_conversations()
            elif self.action == "clear":
                return self._clear_conversations()
            elif self.action == "export":
                return self._export_conversations()
            elif self.action == "search":
                return self._search_conversations()
            elif self.action == "stats":
                return self._show_stats()
            elif self.action == "delete":
                return self._delete_conversation()
            else:
                display_error("Unknown action", f"Action: {self.action}")
                return False

        except Exception as e:
            display_error(f"Memory {self.action} failed", e)
            logger.exception(f"Memory {self.action} error")
            return False

    def _list_conversations(self) -> bool:
        """List conversations."""
        conversations = self.memory_manager.list_conversations(
            role=self.role,
            limit=self.limit,
        )

        if not conversations:
            display_info("No conversations found")
            return True

        # Prepare table data
        rows = []
        for conv in conversations:
            created = datetime.fromisoformat(conv["created_at"])
            updated = datetime.fromisoformat(conv["updated_at"])

            rows.append(
                [
                    conv["id"][:8] + "...",
                    conv["title"][:40] + "..." if len(conv["title"]) > 40 else conv["title"],
                    conv.get("role", "general"),
                    str(conv.get("message_count", 0)),
                    created.strftime("%Y-%m-%d %H:%M"),
                    updated.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        display_table(
            title=f"Conversations ({len(conversations)})",
            columns=["ID", "Title", "Role", "Messages", "Created", "Updated"],
            rows=rows,
        )

        return True

    def _clear_conversations(self) -> bool:
        """Clear all conversations."""
        if not confirm_action("⚠️  Delete ALL conversations? This cannot be undone"):
            display_info("Operation cancelled")
            return True

        count = self.memory_manager.clear_all()
        display_success("Conversations cleared", f"Deleted {count} conversations")
        return True

    def _export_conversations(self) -> bool:
        """Export conversations."""
        if not self.output:
            display_error("Export requires --output path")
            return False

        # Determine conversations to export
        conv_ids = None
        if self.conv_id:
            conv_ids = [self.conv_id]

        success = self.memory_manager.export_conversations(
            output_path=self.output,
            format=self.format,
            conv_ids=conv_ids,
        )

        if success:
            display_success(
                "Conversations exported",
                f"Format: {self.format}\nOutput: {self.output}",
            )
        else:
            display_error("Export failed")

        return success

    def _search_conversations(self) -> bool:
        """Search conversations."""
        if not self.query:
            display_error("Search requires --query")
            return False

        results = self.memory_manager.search_conversations(self.query)

        if not results:
            display_info(f"No results for: {self.query}")
            return True

        # Prepare table data
        rows = []
        for conv in results:
            created = datetime.fromisoformat(conv["created_at"])
            match_type = conv.get("match_type", "unknown")

            rows.append(
                [
                    conv["id"][:8] + "...",
                    conv["title"][:40] + "..." if len(conv["title"]) > 40 else conv["title"],
                    conv.get("role", "general"),
                    match_type,
                    created.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        display_table(
            title=f"Search Results for '{self.query}' ({len(results)})",
            columns=["ID", "Title", "Role", "Match", "Created"],
            rows=rows,
        )

        return True

    def _show_stats(self) -> bool:
        """Show memory statistics."""
        stats = self.memory_manager.get_stats()

        display_info("Memory Statistics\n")

        # Basic stats
        basic_rows = [
            ["Total Conversations", str(stats["total_conversations"])],
            ["Total Messages", str(stats["total_messages"])],
            ["Storage Size", f"{stats['storage_size_mb']} MB"],
        ]

        display_table(
            title="Overview",
            columns=["Metric", "Value"],
            rows=basic_rows,
        )

        # By role
        if stats["conversations_by_role"]:
            role_rows = [
                [role, str(count)]
                for role, count in sorted(
                    stats["conversations_by_role"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ]

            print()  # Spacing
            display_table(
                title="Conversations by Role",
                columns=["Role", "Count"],
                rows=role_rows,
            )

        return True

    def _delete_conversation(self) -> bool:
        """Delete a specific conversation."""
        if not self.conv_id:
            display_error("Delete requires --conv-id")
            return False

        # Load conversation to show details
        conv = self.memory_manager.load_conversation(self.conv_id)
        if not conv:
            display_error("Conversation not found", f"ID: {self.conv_id}")
            return False

        display_info(f"Conversation: {conv.title}")
        display_info(f"Messages: {conv.message_count()}")
        display_info(f"Created: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if not confirm_action("⚠️  Delete this conversation?"):
            display_info("Operation cancelled")
            return True

        success = self.memory_manager.delete_conversation(self.conv_id)

        if success:
            display_success("Conversation deleted", f"ID: {self.conv_id}")
        else:
            display_error("Failed to delete conversation")

        return success
