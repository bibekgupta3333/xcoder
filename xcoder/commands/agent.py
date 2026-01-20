"""
Agent Command Implementation

Handles agent execution and interactive mode.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from xcoder import get_logger
from xcoder.memory import Conversation, MemoryManager, Message, MessageRole
from xcoder.rag import Embedder, VectorStore
from xcoder.services import OllamaService
from xcoder.utils import (
    confirm_action,
    create_spinner,
    display_error,
    display_info,
    display_markdown,
    display_success,
    display_warning,
    prompt_input,
    prompt_select,
)

logger = get_logger(__name__)


class AgentCommand:
    """Run XCoder agent for coding tasks."""

    SLASH_COMMANDS = {
        "/help": "Show available commands",
        "/exit": "Exit interactive mode",
        "/quit": "Exit interactive mode",
        "/clear": "Clear conversation history",
        "/save": "Save current conversation",
        "/context": "Show current context",
        "/role": "Change agent role",
        "/model": "Change LLM model",
    }

    SYSTEM_PROMPTS = {
        "general": "You are XCoder, an expert AI coding assistant. Help users with coding tasks, provide clear explanations, and generate high-quality code.",
        "backend": "You are a backend development expert. Focus on server-side logic, APIs, databases, and system architecture.",
        "frontend": "You are a frontend development expert. Focus on UI/UX, React, TypeScript, and modern web technologies.",
        "devops": "You are a DevOps expert. Focus on CI/CD, infrastructure, containers, and deployment automation.",
        "testing": "You are a testing expert. Focus on unit tests, integration tests, test automation, and quality assurance.",
        "documentation": "You are a technical documentation expert. Focus on clear, comprehensive documentation and code comments.",
    }

    def __init__(
        self,
        task: Optional[str] = None,
        role: Optional[str] = None,
        model: Optional[str] = None,
        context_files: Optional[List[Path]] = None,
        interactive: bool = False,
        path: Optional[Path] = None,
    ):
        """
        Initialize AgentCommand.

        Args:
            task: Task to execute (one-shot mode)
            role: Agent role
            model: LLM model to use
            context_files: Additional context files
            interactive: Start in interactive mode
            path: Project path
        """
        self.task = task
        self.role = role or "general"
        self.model_name = model
        self.context_files = context_files or []
        self.interactive = interactive or (task is None)
        self.path = (path or Path.cwd()).resolve()

        # Initialize components
        xcoder_dir = self.path / ".xcoder"
        if not xcoder_dir.exists():
            raise FileNotFoundError(
                f"XCoder not initialized in {self.path}. Run 'xcoder init' first."
            )

        # Initialize memory manager
        memory_dir = xcoder_dir / "memory"
        self.memory_manager = MemoryManager(memory_dir)

        # Initialize LLM service
        self.llm = OllamaService(model=self.model_name or "codellama:7b")

        # Initialize vector store for RAG
        vector_db_path = xcoder_dir / "data" / "vectordb"
        if vector_db_path.exists():
            self.vectorstore = VectorStore(persist_directory=vector_db_path)
            self.embedder = Embedder()
        else:
            self.vectorstore = None
            self.embedder = None

        # Current conversation
        self.conversation: Optional[Conversation] = None

    def execute(self) -> bool:
        """
        Execute agent.

        Returns:
            True if successful
        """
        try:
            if self.interactive:
                return self._run_interactive()
            else:
                return self._run_one_shot()
        except KeyboardInterrupt:
            display_info("\n\nAgent interrupted by user")
            return True
        except Exception as e:
            display_error("Agent execution failed", e)
            logger.exception("Agent execution error")
            return False

    def _run_one_shot(self) -> bool:
        """Execute a single task and exit."""
        display_info(f"Executing task: {self.task}")

        # Create conversation
        title = self.task[:50] + "..." if len(self.task) > 50 else self.task
        self.conversation = self.memory_manager.create_conversation(
            title=title,
            role=self.role,
        )

        # Get relevant context from vector DB
        context = self._get_context(self.task)

        # Create user message
        user_msg = Message(
            role=MessageRole.USER,
            content=self.task,
        )
        self.conversation.add_message(user_msg)

        # Get response from LLM
        with create_spinner("Thinking...") as spinner:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Prepare messages with context
            messages = self.conversation.get_context()
            if context:
                # Prepend context as system message
                context_msg = Message(
                    role=MessageRole.SYSTEM,
                    content=f"Relevant code context:\n{context}",
                )
                messages.insert(0, context_msg)

            response = loop.run_until_complete(
                self.llm.chat(
                    messages=messages,
                    system=self.SYSTEM_PROMPTS.get(self.role, self.SYSTEM_PROMPTS["general"]),
                )
            )

        # Add assistant response
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            content=response,
        )
        self.conversation.add_message(assistant_msg)

        # Save conversation
        self.memory_manager.save_conversation(self.conversation)

        # Display response
        display_markdown(f"## Response\n\n{response}")

        display_success("Task completed!", f"Conversation saved: {self.conversation.id}")
        return True

    def _run_interactive(self) -> bool:
        """Run in interactive mode."""
        display_info(f"🤖 XCoder Agent (Role: {self.role})")
        display_info("Type '/help' for commands, '/exit' to quit\n")

        # Create conversation
        self.conversation = self.memory_manager.create_conversation(
            title=f"Interactive session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            role=self.role,
        )

        while True:
            try:
                # Get user input
                user_input = prompt_input("You", default="")

                if not user_input.strip():
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    if not self._handle_slash_command(user_input):
                        break  # Exit
                    continue

                # Add user message
                user_msg = Message(
                    role=MessageRole.USER,
                    content=user_input,
                )
                self.conversation.add_message(user_msg)

                # Get relevant context
                context = self._get_context(user_input)

                # Get response from LLM
                print("🤖 Agent: ", end="", flush=True)

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Stream response
                full_response = ""
                messages = self.conversation.get_context(max_messages=10)

                if context:
                    context_msg = Message(
                        role=MessageRole.SYSTEM,
                        content=f"Relevant code context:\n{context}",
                    )
                    messages.insert(0, context_msg)

                async def stream_response():
                    nonlocal full_response
                    async for chunk in self.llm.chat_stream(
                        messages=messages,
                        system=self.SYSTEM_PROMPTS.get(self.role, self.SYSTEM_PROMPTS["general"]),
                    ):
                        print(chunk, end="", flush=True)
                        full_response += chunk
                    print()  # Newline after response

                loop.run_until_complete(stream_response())

                # Add assistant response
                assistant_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                )
                self.conversation.add_message(assistant_msg)

                # Auto-save conversation
                self.memory_manager.save_conversation(self.conversation)

            except KeyboardInterrupt:
                print()  # Newline
                if confirm_action("Exit interactive mode?"):
                    break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                display_error("Error", e)

        display_success("Conversation saved", f"ID: {self.conversation.id}")
        return True

    def _handle_slash_command(self, command: str) -> bool:
        """
        Handle slash commands.

        Args:
            command: Slash command

        Returns:
            True to continue, False to exit
        """
        cmd = command.split()[0].lower()

        if cmd in ["/exit", "/quit"]:
            return False

        elif cmd == "/help":
            display_info("Available commands:")
            for cmd_name, cmd_help in self.SLASH_COMMANDS.items():
                print(f"  {cmd_name:15} - {cmd_help}")
            print()

        elif cmd == "/clear":
            if confirm_action("Clear conversation history?"):
                self.conversation.messages.clear()
                display_success("Conversation cleared")

        elif cmd == "/save":
            self.memory_manager.save_conversation(self.conversation)
            display_success("Conversation saved", f"ID: {self.conversation.id}")

        elif cmd == "/context":
            recent = self.conversation.get_context(max_messages=5)
            display_info(f"Recent messages ({len(recent)}):")
            for i, msg in enumerate(recent, 1):
                role_icon = "👤" if msg.role == MessageRole.USER else "🤖"
                print(f"{i}. {role_icon} {msg.content[:50]}...")
            print()

        elif cmd == "/role":
            roles = list(self.SYSTEM_PROMPTS.keys())
            new_role = prompt_select("Select role", roles, default=self.role)
            self.role = new_role
            display_success("Role changed", f"Now using: {new_role}")

        elif cmd == "/model":
            # Get available models
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            models = loop.run_until_complete(self.llm.list_models())
            if models:
                model_names = [m.get("name", "") for m in models]
                new_model = prompt_select("Select model", model_names)
                self.llm.model = new_model
                display_success("Model changed", f"Now using: {new_model}")
            else:
                display_warning("No models available")

        else:
            display_warning(f"Unknown command: {cmd}")
            display_info("Type '/help' for available commands")

        return True

    def _get_context(self, query: str) -> str:
        """
        Get relevant context from vector DB.

        Args:
            query: User query

        Returns:
            Relevant context string
        """
        if not self.vectorstore or not self.embedder:
            return ""

        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_sync(query)
            if not query_embedding:
                return ""

            # Search vector DB
            results = self.vectorstore.search(
                query_embedding=query_embedding,
                n_results=5,
            )

            if not results:
                return ""

            # Format context
            context_parts = []
            for i, result in enumerate(results, 1):
                file_path = result["metadata"].get("file_path", "unknown")
                chunk_type = result["metadata"].get("chunk_type", "code")
                content = result["document"]

                context_parts.append(f"[{i}] {file_path} ({chunk_type}):\n{content}\n")

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return ""
