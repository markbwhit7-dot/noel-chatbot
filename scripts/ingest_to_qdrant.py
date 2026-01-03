"""
Ingest chunked PDF content into Qdrant vector database.

Uses sentence-transformers for FREE local embeddings (no API key needed).
Model: BAAI/bge-large-en-v1.5 (1024 dimensions, high accuracy)

Usage:
    python ingest_to_qdrant.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)
from sentence_transformers import SentenceTransformer

# Configuration
CHUNKS_JSON = "/home/mark/chunks_for_qdrant.json"
COLLECTION_NAME = "noel_whittaker_docs"

# Using bge-large-en-v1.5: 1024 dimensions, high accuracy
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
EMBEDDING_DIMENSION = 1024
BATCH_SIZE = 32

# Qdrant Cloud credentials
QDRANT_URL = "https://2f62aaa8-2cef-4634-8ab5-4aacc1b9cd68.sa-east-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.DaODSsMZPd3vcsweeNSF8kcgokcWQLLgrlP5ONw4Ow4"


def load_chunks(path: str) -> List[Dict[str, Any]]:
    """Load chunks from JSON file, filtering out index content."""
    with open(path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Filter out index chunks (we used them for topic tagging already)
    filtered = [c for c in chunks if c["metadata"]["content_type"] != "index"]
    print(f"Loaded {len(chunks)} chunks, filtered to {len(filtered)} (excluded index)")
    return filtered


def setup_collection(qdrant: QdrantClient) -> None:
    """Create or recreate the Qdrant collection."""
    collections = qdrant.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if exists:
        print(f"Collection '{COLLECTION_NAME}' exists. Recreating...")
        qdrant.delete_collection(COLLECTION_NAME)

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=Distance.COSINE,
        ),
    )

    # Create payload indexes for filtered searches
    qdrant.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="section",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    qdrant.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="content_type",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    qdrant.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="chapter_title",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    print(f"Created collection '{COLLECTION_NAME}' with indexes")


def ingest_chunks(
    chunks: List[Dict[str, Any]],
    model: SentenceTransformer,
    qdrant: QdrantClient,
) -> None:
    """Ingest all chunks into Qdrant with embeddings."""
    total = len(chunks)
    points = []

    # Get all texts
    texts = [c["text"] for c in chunks]

    print(f"Generating embeddings for {total} chunks...")
    # Encode all at once (sentence-transformers handles batching internally)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    for chunk, embedding in zip(chunks, embeddings):
        point = PointStruct(
            id=chunk["id"],
            vector=embedding.tolist(),
            payload={
                "text": chunk["text"],
                "source": chunk["metadata"]["source"],
                "chapter_title": chunk["metadata"]["chapter_title"],
                "section": chunk["metadata"]["section"],
                "page_start": chunk["metadata"]["page_start"],
                "page_end": chunk["metadata"]["page_end"],
                "chunk_page": chunk["metadata"]["chunk_page"],
                "chunk_index": chunk["metadata"]["chunk_index"],
                "total_chunks": chunk["metadata"]["total_chunks"],
                "topics": chunk["metadata"]["topics"],
                "content_type": chunk["metadata"]["content_type"],
            },
        )
        points.append(point)

    # Upsert all points
    print(f"Uploading {len(points)} points to Qdrant...")
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )
    print("Upload complete!")


def verify_ingestion(qdrant: QdrantClient, model: SentenceTransformer) -> None:
    """Verify the ingestion by checking collection stats and running test search."""
    info = qdrant.get_collection(COLLECTION_NAME)
    print(f"\n=== Collection Stats ===")
    print(f"Points count: {info.points_count}")
    print(f"Status: {info.status}")

    # Sample search to verify
    print("\n=== Sample Search: 'How does salary sacrifice work?' ===")
    query_embedding = model.encode("How does salary sacrifice work?").tolist()

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=3,
    )

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result.score:.4f}")
        print(f"   Chapter: {result.payload['chapter_title']}")
        print(f"   Section: {result.payload['section']}")
        topics = result.payload.get('topics', [])
        print(f"   Topics: {topics[:3] if topics else 'None'}...")
        print(f"   Text: {result.payload['text'][:150]}...")


def main():
    print("=== Qdrant Ingestion Script ===")
    print(f"Qdrant URL: {QDRANT_URL}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Embedding model: {EMBEDDING_MODEL} (local, free)")
    print()

    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Initialize Qdrant client
    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    # Load chunks
    chunks = load_chunks(CHUNKS_JSON)

    # Setup collection
    setup_collection(qdrant)

    # Ingest
    ingest_chunks(chunks, model, qdrant)

    # Verify
    verify_ingestion(qdrant, model)

    print("\n✓ Ingestion complete!")


if __name__ == "__main__":
    main()
