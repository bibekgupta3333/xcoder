"""
Ragify Command Implementation

Handles code vectorization and RAG indexing.
"""

import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

from xcoder import get_logger
from xcoder.rag import CodeChunker, Embedder, VectorStore
from xcoder.utils import (confirm_action, create_progress, create_spinner,
                          display_error, display_info, display_success,
                          display_table, display_warning)

logger = get_logger(__name__)


class RagifyCommand:
    """Vectorize codebase for RAG."""
    
    DEFAULT_IGNORE_PATTERNS = [
        ".git",
        ".xcoder",
        "node_modules",
        "__pycache__",
        "*.pyc",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
        ".next",
        "target",
        "vendor",
        ".gradle",
        "*.min.js",
        "*.bundle.js",
    ]
    
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "shell",
        ".bash": "shell",
        ".md": "markdown",
        ".txt": "text",
    }
    
    def __init__(
        self,
        path: Path,
        watch: bool = False,
        force: bool = False,
        dry_run: bool = False,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize RagifyCommand.
        
        Args:
            path: Path to vectorize
            watch: Watch for changes and auto-update
            force: Force re-vectorization of all files
            dry_run: Preview what will be vectorized without doing it
            include: Additional patterns to include
            exclude: Additional patterns to exclude
            model: Embedding model to use
        """
        self.path = path.resolve()
        self.watch = watch
        self.force = force
        self.dry_run = dry_run
        self.include_patterns = include or []
        self.exclude_patterns = exclude or []
        self.model = model
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        chunk_size = self.config.get("rag", {}).get("chunk_size", 1000)
        chunk_overlap = self.config.get("rag", {}).get("chunk_overlap", 200)
        embedding_model = self.model or self.config.get("rag", {}).get("embedding_model", "nomic-embed-text")
        
        self.chunker = CodeChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        self.embedder = Embedder(model=embedding_model)
        
        # Initialize vector store
        xcoder_dir = self.path / ".xcoder"
        if not xcoder_dir.exists():
            raise FileNotFoundError(
                f"XCoder not initialized in {self.path}. Run 'xcoder init' first."
            )
        
        vector_db_path = xcoder_dir / "data" / "vectordb"
        vector_db_path.mkdir(parents=True, exist_ok=True)
        self.vectorstore = VectorStore(persist_directory=vector_db_path)
    
    def execute(self) -> bool:
        """
        Execute vectorization.
        
        Returns:
            True if successful
        """
        try:
            if self.dry_run:
                return self._run_dry_run()
            
            if self.watch:
                return self._run_watch_mode()
            
            return self._run_vectorization()
            
        except Exception as e:
            display_error("Ragify failed", e)
            logger.exception("Ragify execution failed")
            return False
    
    def _run_vectorization(self) -> bool:
        """Run the vectorization process."""
        start_time = time.time()
        
        display_info(f"Vectorizing codebase: {self.path}")
        
        # Scan files
        files = self._scan_files()
        
        if not files:
            display_warning("No files found to vectorize")
            return True
        
        display_info(f"Found {len(files)} files to process")
        
        # Process files
        stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "files_skipped": 0,
            "errors": 0,
        }
        
        with create_progress("Vectorizing files...") as progress:
            task = progress.add_task("Processing...", total=len(files))
            
            for file_path in files:
                try:
                    result = self._process_file(file_path)
                    stats["files_processed"] += 1
                    stats["chunks_created"] += result["chunks"]
                    stats["embeddings_generated"] += result["embeddings"]
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    stats["errors"] += 1
                finally:
                    progress.update(task, advance=1)
        
        # Display statistics
        elapsed = time.time() - start_time
        self._display_statistics(stats, elapsed)
        
        # Show vector store stats
        vs_stats = self.vectorstore.get_stats()
        display_info(
            f"Vector store: {vs_stats['total_chunks']} chunks from {vs_stats['total_files']} files"
        )
        
        display_success("Vectorization complete!", f"Processed in {elapsed:.2f}s")
        return True
    
    def _run_dry_run(self) -> bool:
        """Preview what will be vectorized."""
        display_info("DRY RUN MODE - No changes will be made")
        
        files = self._scan_files()
        
        if not files:
            display_warning("No files found to vectorize")
            return True
        
        # Group files by language
        files_by_lang = defaultdict(list)
        for file_path in files:
            ext = file_path.suffix.lower()
            lang = self.LANGUAGE_EXTENSIONS.get(ext, "unknown")
            files_by_lang[lang].append(file_path)
        
        # Display summary
        display_info(f"Would process {len(files)} files:")
        
        rows = []
        for lang, lang_files in sorted(files_by_lang.items()):
            rows.append([lang.capitalize(), str(len(lang_files))])
        
        display_table(
            title="Files by Language",
            columns=["Language", "Count"],
            rows=rows,
        )
        
        # Show sample files
        display_info("\nSample files (first 10):")
        for i, file_path in enumerate(files[:10], 1):
            relative_path = file_path.relative_to(self.path)
            print(f"  {i}. {relative_path}")
        
        if len(files) > 10:
            display_info(f"\n... and {len(files) - 10} more files")
        
        return True
    
    def _run_watch_mode(self) -> bool:
        """Run in watch mode for continuous updates."""
        display_info("Watch mode not yet implemented")
        display_warning("Use 'xcoder ragify' without --watch for now")
        return False
    
    def _scan_files(self) -> List[Path]:
        """
        Scan directory for files to vectorize.
        
        Returns:
            List of file paths
        """
        files = []
        ignore_patterns = self._get_ignore_patterns()
        
        for file_path in self.path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Check if file should be ignored
            if self._should_ignore(file_path, ignore_patterns):
                continue
            
            # Check if extension is supported
            ext = file_path.suffix.lower()
            if ext not in self.LANGUAGE_EXTENSIONS:
                continue
            
            # Apply include/exclude patterns
            if self.include_patterns and not any(
                file_path.match(pattern) for pattern in self.include_patterns
            ):
                continue
            
            if self.exclude_patterns and any(
                file_path.match(pattern) for pattern in self.exclude_patterns
            ):
                continue
            
            files.append(file_path)
        
        return sorted(files)
    
    def _process_file(self, file_path: Path) -> Dict[str, int]:
        """
        Process a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with processing statistics
        """
        ext = file_path.suffix.lower()
        language = self.LANGUAGE_EXTENSIONS.get(ext, "unknown")
        
        # Check if file needs update
        if not self.force:
            existing_chunks = self.vectorstore.get_by_file(str(file_path))
            if existing_chunks:
                # TODO: Implement hash-based change detection
                # For now, skip if already indexed
                logger.debug(f"Skipping {file_path} (already indexed)")
                return {"chunks": 0, "embeddings": 0}
        
        # Chunk the file
        chunks = self.chunker.chunk_file(file_path, language)
        
        if not chunks:
            logger.warning(f"No chunks created for {file_path}")
            return {"chunks": 0, "embeddings": 0}
        
        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed_batch_sync(texts)
        
        # Add to vector store
        added = self.vectorstore.add_chunks(chunks, embeddings)
        
        return {"chunks": len(chunks), "embeddings": added}
    
    def _should_ignore(self, file_path: Path, ignore_patterns: List[str]) -> bool:
        """Check if file should be ignored."""
        relative_path = file_path.relative_to(self.path)
        path_str = str(relative_path)
        
        for pattern in ignore_patterns:
            # Check if any part of the path matches the pattern
            if pattern.startswith("*."):
                # Extension pattern
                if file_path.suffix == pattern[1:]:
                    return True
            elif pattern in path_str:
                # Substring match
                return True
            elif file_path.match(pattern):
                # Glob pattern
                return True
        
        return False
    
    def _get_ignore_patterns(self) -> List[str]:
        """Get combined ignore patterns from config and defaults."""
        config_patterns = self.config.get("ignore_patterns", [])
        return list(set(self.DEFAULT_IGNORE_PATTERNS + config_patterns + self.exclude_patterns))
    
    def _load_config(self) -> Dict[str, Any]:
        """Load .xcoderules configuration."""
        config_path = self.path / ".xcoderules"
        
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _display_statistics(self, stats: Dict[str, int], elapsed: float):
        """Display vectorization statistics."""
        rows = [
            ["Files Processed", str(stats["files_processed"])],
            ["Chunks Created", str(stats["chunks_created"])],
            ["Embeddings Generated", str(stats["embeddings_generated"])],
            ["Files Skipped", str(stats["files_skipped"])],
            ["Errors", str(stats["errors"])],
            ["Time Elapsed", f"{elapsed:.2f}s"],
        ]
        
        if elapsed > 0 and stats["files_processed"] > 0:
            rate = stats["files_processed"] / elapsed
            rows.append(["Processing Rate", f"{rate:.1f} files/s"])
        
        display_table(
            title="Vectorization Statistics",
            columns=["Metric", "Value"],
            rows=rows,
        )
        )
