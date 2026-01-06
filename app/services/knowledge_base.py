"""
Knowledge base management service for loading and organizing PDF content.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from .pdf_processor import PDFProcessor
from .vector_store import VectorStore
from .advanced_pdf_extractor import AdvancedPDFExtractor


class KnowledgeBase:
    """Manages loading and organizing class materials and assignments from PDFs."""

    def __init__(self, data_dir: str, use_vector_store: bool = True):
        """
        Initialize knowledge base.

        Args:
            data_dir: Root directory containing PDF files
            use_vector_store: Whether to use vector store for semantic search
        """
        self.data_dir = Path(data_dir)
        self.processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
        self.advanced_extractor = AdvancedPDFExtractor()  # For assignments
        self.materials: Dict[str, str] = {}  # filename: content
        self.assignments: Dict[str, str] = {}  # filename: content
        self.assignment_structures: Dict[str, Dict] = {}  # filename: structured content
        self.load_errors: List[str] = []
        self.use_vector_store = use_vector_store

        # Initialize vector store if enabled
        self.vector_store: Optional[VectorStore] = None
        if self.use_vector_store:
            self.vector_store = VectorStore(persist_directory=str(self.data_dir / "chromadb"))

    def load_pdfs(self):
        """
        Load and process all PDFs from materials and assignments directories.

        This method is called at application startup to load all PDF content
        into memory for fast access.
        """
        print("=" * 60)
        print("Loading PDFs into knowledge base...")
        print("=" * 60)

        # Load class materials
        materials_dir = self.data_dir / "pdfs" / "materials"
        if materials_dir.exists():
            self._load_directory(materials_dir, self.materials, "Class Materials")
        else:
            print(f"⚠️  Materials directory not found: {materials_dir}")
            print("   Please create it and add your class material PDFs.")

        # Load assignments
        assignments_dir = self.data_dir / "pdfs" / "assignments"
        if assignments_dir.exists():
            self._load_directory(assignments_dir, self.assignments, "Assignments")
        else:
            print(f"⚠️  Assignments directory not found: {assignments_dir}")
            print("   Please create it and add your assignment PDFs.")

        # Summary
        print("=" * 60)
        print(f"✓ Loaded {len(self.materials)} class material PDF(s)")
        print(f"✓ Loaded {len(self.assignments)} assignment PDF(s)")
        if self.load_errors:
            print(f"⚠️  {len(self.load_errors)} error(s) occurred:")
            for error in self.load_errors:
                print(f"   - {error}")
        print("=" * 60)

    def _load_directory(self, directory: Path, storage: Dict[str, str], category: str):
        """
        Load all PDFs from a specific directory.

        Args:
            directory: Directory to scan for PDFs
            storage: Dictionary to store loaded content
            category: Category name for logging
        """
        pdf_files = list(directory.glob("*.pdf"))

        if not pdf_files:
            print(f"\n📁 {category}: No PDF files found in {directory}")
            return

        print(f"\n📁 {category} ({len(pdf_files)} file(s)):")

        # Check if this is assignments directory (use advanced extractor)
        is_assignment = "assignment" in category.lower()

        for pdf_file in pdf_files:
            try:
                print(f"   Loading: {pdf_file.name}...", end=" ")

                if is_assignment:
                    # Use advanced extractor for assignments
                    self._load_assignment_pdf(pdf_file, storage, category)
                else:
                    # Use regular extractor for class materials
                    self._load_material_pdf(pdf_file, storage, category)

            except Exception as e:
                print(f"✗ ERROR")
                error_msg = f"{pdf_file.name}: {str(e)}"
                self.load_errors.append(error_msg)
                print(f"   Error details: {str(e)}")

    def _load_material_pdf(self, pdf_file: Path, storage: Dict[str, str], category: str):
        """Load class material PDF with regular chunking."""
        # Extract text from PDF
        content = self.processor.extract_text(str(pdf_file))

        if not content or len(content.strip()) < 10:
            print("⚠️  SKIPPED (no readable content)")
            self.load_errors.append(f"{pdf_file.name}: No readable content")
            return

        # Store content
        storage[pdf_file.name] = content

        # If using vector store, chunk and add to ChromaDB
        if self.use_vector_store and self.vector_store:
            chunks = self.processor.chunk_text(content)

            # Prepare metadata and IDs for each chunk
            chunk_ids = []
            chunk_metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{pdf_file.stem}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_metadatas.append({
                    "source": pdf_file.name,
                    "category": category,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "type": "material"
                })

            # Add to vector store
            self.vector_store.add_documents(
                texts=chunks,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
            print(f"✓ ({len(content)} chars, {len(chunks)} chunks)")
        else:
            print(f"✓ ({len(content)} chars)")

    def _load_assignment_pdf(self, pdf_file: Path, storage: Dict[str, str], category: str):
        """Load assignment PDF with advanced structured extraction."""
        # Extract structured content
        structured_content = self.advanced_extractor.extract_structured_content(str(pdf_file))

        # Store full text
        content = structured_content['full_text']
        if not content or len(content.strip()) < 10:
            print("⚠️  SKIPPED (no readable content)")
            self.load_errors.append(f"{pdf_file.name}: No readable content")
            return

        storage[pdf_file.name] = content
        self.assignment_structures[pdf_file.name] = structured_content

        # Extract images if any
        if structured_content.get('images'):
            images_dir = self.data_dir / "extracted_images" / pdf_file.stem
            try:
                images_info = self.advanced_extractor.extract_images(
                    str(pdf_file),
                    str(images_dir)
                )
                structured_content['images_info'] = images_info
            except Exception as e:
                print(f"⚠️  Image extraction failed: {str(e)}")

        # Create intelligent chunks
        if self.use_vector_store and self.vector_store:
            chunks_data = self.advanced_extractor.create_question_chunks(structured_content)

            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []

            for i, chunk_data in enumerate(chunks_data):
                chunk_id = f"{pdf_file.stem}_q{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk_data['text'])

                # Rich metadata
                metadata = {
                    "source": pdf_file.name,
                    "category": category,
                    "chunk_index": i,
                    "total_chunks": len(chunks_data),
                    **chunk_data['metadata']
                }
                chunk_metadatas.append(metadata)

            # Add to vector store
            self.vector_store.add_documents(
                texts=chunk_texts,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )

            # Print summary
            num_questions = len([c for c in chunks_data if c['metadata']['type'] == 'question'])
            num_scenarios = len([c for c in chunks_data if c['metadata']['type'] == 'scenario'])
            num_tables = len(structured_content.get('tables', []))
            num_images = len(structured_content.get('images', []))

            summary_parts = [f"{num_questions}Q"]
            if num_scenarios > 0:
                summary_parts.append(f"{num_scenarios}S")
            if num_tables > 0:
                summary_parts.append(f"{num_tables}T")
            if num_images > 0:
                summary_parts.append(f"{num_images}I")

            summary = "+".join(summary_parts)
            print(f"✓ ({len(content)} chars, {len(chunks_data)} chunks: {summary})")
        else:
            print(f"✓ ({len(content)} chars)")

    def get_all_context(self) -> str:
        """
        Combine all materials and assignments into a single context string.

        Returns:
            Formatted string with all PDF content
        """
        context_parts = []

        if self.materials:
            context_parts.append("=== CLASS MATERIALS ===\n")
            for filename, content in self.materials.items():
                context_parts.append(f"\n--- {filename} ---\n")
                context_parts.append(content)
                context_parts.append("\n")

        if self.assignments:
            context_parts.append("\n=== ASSIGNMENTS ===\n")
            for filename, content in self.assignments.items():
                context_parts.append(f"\n--- {filename} ---\n")
                context_parts.append(content)
                context_parts.append("\n")

        if not context_parts:
            return "No class materials or assignments have been loaded."

        return "\n".join(context_parts)

    def get_materials_only(self) -> str:
        """
        Get only class materials context.

        Returns:
            Formatted string with class materials
        """
        if not self.materials:
            return "No class materials loaded."

        parts = ["=== CLASS MATERIALS ===\n"]
        for filename, content in self.materials.items():
            parts.append(f"\n--- {filename} ---\n")
            parts.append(content)
            parts.append("\n")

        return "\n".join(parts)

    def get_assignments_only(self) -> str:
        """
        Get only assignments context.

        Returns:
            Formatted string with assignments
        """
        if not self.assignments:
            return "No assignments loaded."

        parts = ["=== ASSIGNMENTS ===\n"]
        for filename, content in self.assignments.items():
            parts.append(f"\n--- {filename} ---\n")
            parts.append(content)
            parts.append("\n")

        return "\n".join(parts)

    def get_summary(self) -> dict:
        """
        Get summary information about loaded PDFs.

        Returns:
            Dictionary with summary statistics
        """
        return {
            "materials_count": len(self.materials),
            "assignments_count": len(self.assignments),
            "total_pdfs": len(self.materials) + len(self.assignments),
            "materials_list": list(self.materials.keys()),
            "assignments_list": list(self.assignments.keys()),
            "errors": self.load_errors,
        }

    def has_content(self) -> bool:
        """
        Check if any PDFs have been loaded.

        Returns:
            True if at least one PDF is loaded, False otherwise
        """
        return len(self.materials) > 0 or len(self.assignments) > 0

    def get_relevant_context(self, query: str, n_results: int = 5) -> str:
        """
        Get relevant context for a query using semantic search (RAG approach).

        Args:
            query: User's question
            n_results: Number of relevant chunks to retrieve

        Returns:
            Formatted string with relevant context from PDFs
        """
        if not self.use_vector_store or not self.vector_store:
            # Fallback to full context if vector store not enabled
            return self.get_all_context()

        # Search for relevant chunks
        results = self.vector_store.search(query, n_results=n_results)

        if not results:
            return "No relevant information found in the class materials."

        # Format results with source attribution
        context_parts = [f"=== RELEVANT CONTEXT (Top {len(results)} matches) ===\n"]

        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            text = result["text"]
            source = metadata.get("source", "Unknown")
            category = metadata.get("category", "Unknown")

            context_parts.append(f"\n[Match {i}] From: {source} ({category})")
            context_parts.append(f"{text}\n")

        return "\n".join(context_parts)
