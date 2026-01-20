"""
Code Chunking Module

Handles intelligent code splitting with language-aware boundaries.
"""

import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from xcoder import get_logger

logger = get_logger(__name__)


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""

    content: str
    file_path: str
    chunk_id: str
    chunk_type: str  # function, class, module, file
    start_line: int
    end_line: int
    language: str
    metadata: Dict[str, Any]
    hash: str


class CodeChunker:
    """Intelligent code chunking with language-aware boundaries."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize CodeChunker.

        Args:
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks for context
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(self, file_path: Path, language: str) -> List[CodeChunk]:
        """
        Chunk a code file intelligently.

        Args:
            file_path: Path to the file
            language: Programming language

        Returns:
            List of code chunks
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            if language == "python":
                return self._chunk_python(file_path, content)
            else:
                return self._chunk_generic(file_path, content, language)

        except Exception as e:
            logger.error(f"Error chunking {file_path}: {e}")
            return []

    def _chunk_python(self, file_path: Path, content: str) -> List[CodeChunk]:
        """
        Chunk Python code using AST analysis.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of code chunks
        """
        chunks = []

        try:
            tree = ast.parse(content)
            lines = content.splitlines()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if node.end_lineno else start_line + 1

                    chunk_content = "\n".join(lines[start_line:end_line])

                    # Skip if chunk is too large, will be handled by generic chunker
                    if len(chunk_content) > self.chunk_size * 2:
                        continue

                    chunk_type = (
                        "function"
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        else "class"
                    )

                    metadata = {
                        "name": node.name,
                        "decorators": [
                            d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list
                        ],
                        "docstring": ast.get_docstring(node),
                    }

                    if isinstance(node, ast.FunctionDef):
                        metadata["args"] = [arg.arg for arg in node.args.args]

                    chunk = CodeChunk(
                        content=chunk_content,
                        file_path=str(file_path),
                        chunk_id=self._generate_chunk_id(
                            file_path, chunk_type, node.name, start_line
                        ),
                        chunk_type=chunk_type,
                        start_line=start_line + 1,
                        end_line=end_line,
                        language="python",
                        metadata=metadata,
                        hash=self._hash_content(chunk_content),
                    )
                    chunks.append(chunk)

            # If no chunks extracted or file has top-level code, add module-level chunk
            if len(chunks) == 0 or len(content) > sum(len(c.content) for c in chunks) * 1.5:
                module_chunk = self._create_module_chunk(file_path, content, "python")
                chunks.insert(0, module_chunk)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}, using generic chunking: {e}")
            return self._chunk_generic(file_path, content, "python")

        return chunks

    def _chunk_generic(self, file_path: Path, content: str, language: str) -> List[CodeChunk]:
        """
        Generic text-based chunking with overlap.

        Args:
            file_path: Path to the file
            content: File content
            language: Programming language

        Returns:
            List of code chunks
        """
        chunks = []
        lines = content.splitlines()

        if len(content) <= self.chunk_size:
            # File is small enough, treat as single chunk
            chunk = CodeChunk(
                content=content,
                file_path=str(file_path),
                chunk_id=self._generate_chunk_id(file_path, "file", "", 1),
                chunk_type="file",
                start_line=1,
                end_line=len(lines),
                language=language,
                metadata={"total_lines": len(lines)},
                hash=self._hash_content(content),
            )
            return [chunk]

        # Split into overlapping chunks
        current_chunk_lines = []
        current_length = 0
        chunk_number = 0
        start_line = 1

        for i, line in enumerate(lines, 1):
            current_chunk_lines.append(line)
            current_length += len(line) + 1  # +1 for newline

            if current_length >= self.chunk_size or i == len(lines):
                chunk_content = "\n".join(current_chunk_lines)
                chunk_number += 1

                chunk = CodeChunk(
                    content=chunk_content,
                    file_path=str(file_path),
                    chunk_id=self._generate_chunk_id(
                        file_path, "chunk", str(chunk_number), start_line
                    ),
                    chunk_type="chunk",
                    start_line=start_line,
                    end_line=i,
                    language=language,
                    metadata={
                        "chunk_number": chunk_number,
                        "total_lines": len(current_chunk_lines),
                    },
                    hash=self._hash_content(chunk_content),
                )
                chunks.append(chunk)

                # Calculate overlap for next chunk
                if i < len(lines):
                    overlap_chars = 0
                    overlap_lines = []
                    for line in reversed(current_chunk_lines):
                        if overlap_chars >= self.overlap:
                            break
                        overlap_lines.insert(0, line)
                        overlap_chars += len(line) + 1

                    current_chunk_lines = overlap_lines
                    current_length = overlap_chars
                    start_line = i - len(overlap_lines) + 1

        return chunks

    def _create_module_chunk(self, file_path: Path, content: str, language: str) -> CodeChunk:
        """Create a module-level chunk for top-level code."""
        lines = content.splitlines()

        return CodeChunk(
            content=content,
            file_path=str(file_path),
            chunk_id=self._generate_chunk_id(file_path, "module", "", 1),
            chunk_type="module",
            start_line=1,
            end_line=len(lines),
            language=language,
            metadata={"total_lines": len(lines)},
            hash=self._hash_content(content),
        )

    def _generate_chunk_id(self, file_path: Path, chunk_type: str, name: str, line: int) -> str:
        """Generate unique chunk ID."""
        base = f"{file_path}:{chunk_type}:{name}:{line}"
        return hashlib.md5(base.encode()).hexdigest()

    def _hash_content(self, content: str) -> str:
        """Generate content hash for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()
