"""
PDF processing service for extracting and cleaning text from PDF files.
"""
import fitz  # PyMuPDF
import re
from typing import List
from pathlib import Path


class PDFProcessor:
    """Handles PDF text extraction and processing."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize PDF processor.

        Args:
            chunk_size: Target size for text chunks (default: 1000 characters)
            chunk_overlap: Overlap between chunks for context (default: 200 characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted and cleaned text

        Raises:
            Exception: If PDF processing fails
        """
        try:
            text = ""
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                try:
                    page_text = page.get_text()
                    text += page_text
                except Exception as e:
                    print(f"Warning: Error extracting text from page {page_num + 1}: {str(e)}")
                    continue

            doc.close()

            # Clean the extracted text
            cleaned_text = self.clean_text(text)

            return cleaned_text

        except Exception as e:
            raise Exception(f"Error processing PDF '{pdf_path}': {str(e)}")

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace and special characters.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)

        # Remove control characters but keep basic punctuation
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Remove excessive special characters while keeping basic ones
        # Keep: letters, numbers, spaces, and basic punctuation
        text = re.sub(r'[^\w\s\.\,\?\!\-\:\;\(\)\[\]\{\}\"\'\n\r]', '', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for better semantic search.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks with overlap
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Get chunk of target size
            end = start + self.chunk_size

            # If not at the end, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within a window
                search_start = max(start + self.chunk_size - 100, start)
                search_end = min(end + 100, len(text))
                chunk_text = text[search_start:search_end]

                # Find last sentence ending
                last_period = chunk_text.rfind('. ')
                last_question = chunk_text.rfind('? ')
                last_exclamation = chunk_text.rfind('! ')

                break_point = max(last_period, last_question, last_exclamation)

                if break_point > 0:
                    end = search_start + break_point + 2  # Include punctuation and space

            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

        return chunks

    def chunk_text_by_sentences(self, text: str, sentences_per_chunk: int = 5) -> List[str]:
        """
        Split text into chunks by sentences for more semantic coherence.

        Args:
            text: Text to chunk
            sentences_per_chunk: Number of sentences per chunk

        Returns:
            List of text chunks
        """
        # Simple sentence splitting (can be improved with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []

        for sentence in sentences:
            current_chunk.append(sentence)

            if len(current_chunk) >= sentences_per_chunk:
                chunks.append(' '.join(current_chunk))
                # Overlap: keep last sentence for context
                current_chunk = [current_chunk[-1]]

        # Add remaining sentences
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validate if a file is a valid PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if valid PDF, False otherwise
        """
        try:
            doc = fitz.open(pdf_path)
            page_count = doc.page_count
            doc.close()
            return page_count > 0
        except:
            return False

    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get metadata information from a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with PDF metadata
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = {
                'page_count': doc.page_count,
                'title': doc.metadata.get('title', 'Unknown'),
                'author': doc.metadata.get('author', 'Unknown'),
                'subject': doc.metadata.get('subject', 'Unknown'),
            }
            doc.close()
            return metadata
        except Exception as e:
            return {'error': str(e)}
