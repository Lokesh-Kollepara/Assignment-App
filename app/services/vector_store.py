"""
Vector store service using ChromaDB for semantic search.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path


class VectorStore:
    """Manages vector embeddings and semantic search using ChromaDB."""

    def __init__(self, persist_directory: str = "data/chromadb"):
        """
        Initialize ChromaDB vector store.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Create or get collection
        # Using default embedding function (all-MiniLM-L6-v2)
        self.collection = self.client.get_or_create_collection(
            name="pdf_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

        print(f"✓ Vector Store initialized (ChromaDB)")
        print(f"  Collection: pdf_knowledge_base")
        print(f"  Documents in collection: {self.collection.count()}")

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            texts: List of text chunks to embed
            metadatas: List of metadata dicts for each chunk
            ids: List of unique IDs for each chunk
        """
        if not texts:
            print("⚠️  No documents to add to vector store")
            return

        try:
            # Add documents to ChromaDB (embeddings generated automatically)
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✓ Added {len(texts)} document chunks to vector store")
        except Exception as e:
            print(f"✗ Error adding documents to vector store: {str(e)}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for relevant documents using semantic similarity.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of relevant document chunks with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata if filter_metadata else None,
            )

            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None,
                    })

            return formatted_results

        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []

    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete and recreate collection
            self.client.delete_collection(name="pdf_knowledge_base")
            self.collection = self.client.get_or_create_collection(
                name="pdf_knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
            print("✓ Vector store cleared")
        except Exception as e:
            print(f"Error clearing vector store: {str(e)}")

    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.

        Returns:
            Dictionary with collection statistics
        """
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name,
        }

    def delete_by_source(self, source: str) -> None:
        """
        Delete all documents from a specific source.

        Args:
            source: Source filename to delete
        """
        try:
            # Get all IDs for this source
            results = self.collection.get(
                where={"source": source}
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                print(f"✓ Deleted {len(results['ids'])} chunks from source: {source}")
        except Exception as e:
            print(f"Error deleting from vector store: {str(e)}")
