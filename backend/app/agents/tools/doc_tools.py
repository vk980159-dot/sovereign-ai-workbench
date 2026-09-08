"""
Document & Knowledge Base Inspection Tools (SIH26117).
Interfaces safely with ChromaDB vector store and supported local document formats.
"""

import os
import hashlib
import json
import csv
from typing import Dict, Any, List, Optional
from app.config import settings, BASE_DIR
from app.database.vector_store import vector_store

try:
    import pypdf
except ImportError:
    pypdf = None


def _find_local_file(filename: str) -> Optional[str]:
    """Resolves filename across authorized directories."""
    clean_name = os.path.basename(filename)
    candidates = [
        os.path.join(settings.DEMO_DATA_DIR, clean_name),
        os.path.join(settings.UPLOAD_DIR, clean_name),
        os.path.join(settings.MULTIMODAL_UPLOAD_DIR, clean_name),
        os.path.join(settings.OUTPUT_DIR, clean_name),
        os.path.join(BASE_DIR, clean_name),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def local_document_search(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Queries local ChromaDB vector store using nomic-embed-text embeddings.
    Returns matched chunks with document provenance and similarity score.
    """
    matches = vector_store.retrieve_context(query=query, top_k=top_k)
    if not matches:
        return {
            "query": query,
            "count": 0,
            "documents": [],
            "message": "No relevant local knowledge-base evidence was found."
        }

    formatted = []
    for m in matches:
        meta = m.get("metadata", {})
        formatted.append({
            "chunk_id": m.get("chunk_id", ""),
            "document_id": meta.get("document_id", ""),
            "filename": meta.get("filename", "unknown"),
            "similarity": m.get("similarity", 0.0),
            "content": m.get("content", "").strip()
        })

    return {
        "query": query,
        "count": len(formatted),
        "documents": formatted,
        "message": f"Retrieved {len(formatted)} relevant evidence chunks from ChromaDB."
    }


def local_document_reader(filename: str, max_characters: int = 10000) -> Dict[str, Any]:
    """
    Reads supported local documents safely from approved directories.
    """
    file_path = _find_local_file(filename)
    if not file_path:
        return {
            "found": False,
            "filename": filename,
            "error": f"Document '{filename}' not found in authorized local storage."
        }

    ext = os.path.splitext(file_path)[1].lower()
    raw_content = ""

    if ext == ".pdf":
        if not pypdf:
            return {"found": False, "filename": filename, "error": "pypdf library unavailable."}
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            pages = [p.extract_text() or "" for p in reader.pages]
            raw_content = "\n\n".join(pages)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()

    truncated = raw_content[:max_characters]
    sha256 = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()

    return {
        "found": True,
        "filename": os.path.basename(file_path),
        "extension": ext,
        "characters": len(raw_content),
        "truncated": len(raw_content) > max_characters,
        "sha256": sha256,
        "content": truncated
    }


def file_metadata(filename: str) -> Dict[str, Any]:
    """Returns safe filesystem and cryptographic metadata."""
    file_path = _find_local_file(filename)
    if not file_path:
        return {"found": False, "filename": filename, "error": "File not found."}

    stat = os.stat(file_path)
    with open(file_path, "rb") as f:
        file_sha256 = hashlib.sha256(f.read()).hexdigest()

    return {
        "found": True,
        "filename": os.path.basename(file_path),
        "size_bytes": stat.st_size,
        "sha256": file_sha256,
        "extension": os.path.splitext(file_path)[1].lower(),
        "modified_at": stat.st_mtime
    }


def text_extractor(filename: str) -> Dict[str, Any]:
    """Extracts raw plain text content from documents."""
    return local_document_reader(filename=filename, max_characters=20000)


def structured_data_reader(filename: str, delimiter: str = ",", max_rows: int = 100) -> Dict[str, Any]:
    """Safely parses structured CSV or JSON files."""
    file_path = _find_local_file(filename)
    if not file_path:
        return {"found": False, "filename": filename, "error": "File not found."}

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"found": True, "format": "json", "data": data}

    if ext == ".csv":
        rows = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)
            for i, r in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(r)
        return {
            "found": True,
            "format": "csv",
            "header": header,
            "row_count": len(rows),
            "rows": rows
        }

    return {"found": False, "error": f"Unsupported structured data extension '{ext}'."}
