"""
Memory Manager

Handles storage and retrieval of conversations.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from xcoder import get_logger

from .conversation import Conversation, Message, MessageRole

logger = get_logger(__name__)


class MemoryManager:
    """Manages conversation memory storage."""
    
    def __init__(self, memory_dir: Path):
        """
        Initialize MemoryManager.
        
        Args:
            memory_dir: Directory to store conversations
        """
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.memory_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        """Load conversation index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self.index = {}
        else:
            self.index = {}
    
    def _save_index(self):
        """Save conversation index."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def create_conversation(self, title: str, role: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            title: Conversation title
            role: Agent role
            
        Returns:
            New conversation
        """
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            title=title,
            role=role,
        )
        
        # Update index
        self.index[conv_id] = {
            "title": title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "role": role,
            "message_count": 0,
        }
        self._save_index()
        
        # Save conversation
        self.save_conversation(conversation)
        
        logger.info(f"Created conversation {conv_id}: {title}")
        return conversation
    
    def save_conversation(self, conversation: Conversation):
        """
        Save a conversation to disk.
        
        Args:
            conversation: Conversation to save
        """
        conv_file = self.memory_dir / f"{conversation.id}.json"
        try:
            with open(conv_file, "w") as f:
                json.dump(conversation.to_dict(), f, indent=2)
            
            # Update index
            self.index[conversation.id] = {
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "role": conversation.role,
                "message_count": conversation.message_count(),
                "tags": conversation.tags,
            }
            self._save_index()
            
            logger.debug(f"Saved conversation {conversation.id}")
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id}: {e}")
    
    def load_conversation(self, conv_id: str) -> Optional[Conversation]:
        """
        Load a conversation from disk.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            Conversation or None if not found
        """
        conv_file = self.memory_dir / f"{conv_id}.json"
        if not conv_file.exists():
            logger.warning(f"Conversation {conv_id} not found")
            return None
        
        try:
            with open(conv_file, "r") as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading conversation {conv_id}: {e}")
            return None
    
    def list_conversations(
        self,
        role: Optional[str] = None,
        tag: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List conversations with optional filters.
        
        Args:
            role: Filter by agent role
            tag: Filter by tag
            limit: Maximum number of results
            
        Returns:
            List of conversation summaries
        """
        conversations = []
        
        for conv_id, info in self.index.items():
            # Apply filters
            if role and info.get("role") != role:
                continue
            if tag and tag not in info.get("tags", []):
                continue
            
            conversations.append({
                "id": conv_id,
                **info,
            })
        
        # Sort by updated_at (most recent first)
        conversations.sort(
            key=lambda x: x.get("updated_at", ""),
            reverse=True,
        )
        
        if limit:
            conversations = conversations[:limit]
        
        return conversations
    
    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """
        Search conversations by title or content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching conversations
        """
        results = []
        query_lower = query.lower()
        
        for conv_id, info in self.index.items():
            # Search in title
            if query_lower in info.get("title", "").lower():
                results.append({
                    "id": conv_id,
                    **info,
                    "match_type": "title",
                })
                continue
            
            # Search in conversation content
            conversation = self.load_conversation(conv_id)
            if conversation:
                for message in conversation.messages:
                    if query_lower in message.content.lower():
                        results.append({
                            "id": conv_id,
                            **info,
                            "match_type": "content",
                        })
                        break
        
        return results
    
    def delete_conversation(self, conv_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conv_id: Conversation ID
            
        Returns:
            True if deleted successfully
        """
        conv_file = self.memory_dir / f"{conv_id}.json"
        
        if not conv_file.exists():
            logger.warning(f"Conversation {conv_id} not found")
            return False
        
        try:
            conv_file.unlink()
            if conv_id in self.index:
                del self.index[conv_id]
                self._save_index()
            logger.info(f"Deleted conversation {conv_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conv_id}: {e}")
            return False
    
    def clear_all(self) -> int:
        """
        Clear all conversations.
        
        Returns:
            Number of conversations deleted
        """
        count = 0
        for conv_id in list(self.index.keys()):
            if self.delete_conversation(conv_id):
                count += 1
        return count
    
    def export_conversations(
        self,
        output_path: Path,
        format: str = "json",
        conv_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Export conversations to a file.
        
        Args:
            output_path: Output file path
            format: Export format (json, markdown, csv)
            conv_ids: Specific conversation IDs to export (None = all)
            
        Returns:
            True if successful
        """
        try:
            if conv_ids is None:
                conv_ids = list(self.index.keys())
            
            conversations = []
            for conv_id in conv_ids:
                conv = self.load_conversation(conv_id)
                if conv:
                    conversations.append(conv)
            
            if format == "json":
                return self._export_json(conversations, output_path)
            elif format == "markdown":
                return self._export_markdown(conversations, output_path)
            elif format == "csv":
                return self._export_csv(conversations, output_path)
            else:
                logger.error(f"Unsupported format: {format}")
                return False
                
        except Exception as e:
            logger.error(f"Error exporting conversations: {e}")
            return False
    
    def _export_json(self, conversations: List[Conversation], output_path: Path) -> bool:
        """Export as JSON."""
        data = [conv.to_dict() for conv in conversations]
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    
    def _export_markdown(self, conversations: List[Conversation], output_path: Path) -> bool:
        """Export as Markdown."""
        lines = ["# XCoder Conversation Export\n\n"]
        
        for conv in conversations:
            lines.append(f"## {conv.title}\n\n")
            lines.append(f"**ID**: {conv.id}  \n")
            lines.append(f"**Created**: {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}  \n")
            lines.append(f"**Role**: {conv.role or 'general'}  \n")
            lines.append(f"**Messages**: {conv.message_count()}\n\n")
            
            for i, msg in enumerate(conv.messages, 1):
                role_emoji = "👤" if msg.role == MessageRole.USER else "🤖"
                lines.append(f"### {role_emoji} Message {i} ({msg.role.value})\n\n")
                lines.append(f"*{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                lines.append(f"{msg.content}\n\n")
                lines.append("---\n\n")
        
        with open(output_path, "w") as f:
            f.writelines(lines)
        return True
    
    def _export_csv(self, conversations: List[Conversation], output_path: Path) -> bool:
        """Export as CSV."""
        import csv
        
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Conversation ID",
                "Title",
                "Role",
                "Message Role",
                "Message Content",
                "Timestamp",
            ])
            
            for conv in conversations:
                for msg in conv.messages:
                    writer.writerow([
                        conv.id,
                        conv.title,
                        conv.role or "general",
                        msg.role.value,
                        msg.content,
                        msg.timestamp.isoformat(),
                    ])
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Statistics dictionary
        """
        total_conversations = len(self.index)
        total_messages = sum(info.get("message_count", 0) for info in self.index.values())
        
        # Count by role
        roles = {}
        for info in self.index.values():
            role = info.get("role", "general")
            roles[role] = roles.get(role, 0) + 1
        
        # Calculate storage size
        storage_size = sum(
            f.stat().st_size
            for f in self.memory_dir.glob("*.json")
        )
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "conversations_by_role": roles,
            "storage_size_bytes": storage_size,
            "storage_size_mb": round(storage_size / 1024 / 1024, 2),
        }
        }
