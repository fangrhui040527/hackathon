"""
knowledge/blob_loader.py
Loads knowledge datasets from Azure Blob Storage with in-memory caching.
Falls back to local JSON files in knowledge_json/ when Blob Storage is unavailable.

Blob container structure (JSON files):
  knowledge/additives.json
  knowledge/dietary_limits.json
  knowledge/drug_food_interactions.json
  knowledge/glycemic_index.json
  knowledge/iarc_carcinogens.json
  knowledge/nova_classification.json

Each knowledge module calls load_knowledge_blob() once on first use.
Data is cached in memory for the lifetime of the process.
"""

import json
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ── Azure Blob config ────────────────────────────────────────────────────
_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
# Uses its own env var to avoid conflict with data_retreive.py's container
_CONTAINER_NAME = os.getenv("AZURE_KNOWLEDGE_CONTAINER_NAME",
                            os.getenv("AZURE_STORAGE_CONTAINER_NAME", "healthlens"))
_BLOB_PREFIX = "knowledge/"  # all knowledge JSONs live under this prefix

# ── Local fallback path ──────────────────────────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOCAL_KNOWLEDGE_DIR = os.path.join(_PROJECT_ROOT, "knowledge_json")

# ── In-memory cache ──────────────────────────────────────────────────────
_CACHE: dict[str, Any] = {}


def _load_from_local(blob_name: str) -> Any:
    """
    Try to load a knowledge JSON file from the local knowledge_json/ directory.
    Returns None if not found.
    """
    local_path = os.path.join(_LOCAL_KNOWLEDGE_DIR, blob_name)
    if os.path.isfile(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            size = os.path.getsize(local_path)
            print(f"[BlobLoader] Loaded from local file: knowledge_json/{blob_name} ({size:,} bytes)")
            return data
        except Exception as e:
            print(f"[BlobLoader] Failed to load local file knowledge_json/{blob_name}: {e}")
    return None


def _load_from_blob(blob_name: str) -> Any:
    """
    Try to load a knowledge JSON file from Azure Blob Storage.
    Returns None if unavailable. Caches failures to avoid repeated slow attempts.
    """
    if not _CONNECTION_STRING:
        return None

    # If a previous blob load already failed, skip Azure entirely for this process
    if _CACHE.get("__blob_unavailable__"):
        return None

    blob_path = f"{_BLOB_PREFIX}{blob_name}"
    try:
        from azure.storage.blob import BlobServiceClient
        client = BlobServiceClient.from_connection_string(_CONNECTION_STRING)
        container = client.get_container_client(_CONTAINER_NAME)
        blob_client = container.get_blob_client(blob_path)

        raw = blob_client.download_blob().readall()
        data = json.loads(raw)
        print(f"[BlobLoader] Loaded from Azure Blob: {blob_path} ({len(raw):,} bytes)")
        return data
    except ImportError:
        print("[BlobLoader] azure-storage-blob not installed — using local files.")
        _CACHE["__blob_unavailable__"] = True
        return None
    except Exception as e:
        error_msg = str(e)
        # If the container doesn't exist, mark blob as unavailable for all future loads
        if "ContainerNotFound" in error_msg or "AuthenticationFailed" in error_msg:
            print(f"[BlobLoader] Azure Blob Storage unavailable — using local files instead.")
            _CACHE["__blob_unavailable__"] = True
        else:
            print(f"[BlobLoader] Failed to load from Blob {blob_path}: {e}")
        return None


def load_knowledge_blob(blob_name: str, fallback: Any = None) -> Any:
    """
    Load a JSON knowledge file. Tries Azure Blob Storage first,
    then falls back to local knowledge_json/ directory, then to the fallback value.

    Args:
        blob_name: Filename (e.g. "additives.json").
        fallback: Value returned if nothing can be loaded. Defaults to None.

    Returns:
        Parsed JSON data (dict or list), or fallback on failure.
    """
    cache_key = blob_name

    # Return cached data if already loaded
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    # Strategy 1: Try Azure Blob Storage
    data = _load_from_blob(blob_name)

    # Strategy 2: Try local knowledge_json/ directory
    if data is None:
        data = _load_from_local(blob_name)

    # Strategy 3: Use fallback
    if data is None:
        if fallback is not None:
            print(f"[BlobLoader] Using empty fallback for {blob_name}")
            data = fallback
        else:
            print(f"[BlobLoader] No data source available for {blob_name}")
            return None

    _CACHE[cache_key] = data
    return data


def clear_cache():
    """Clear all cached knowledge data (forces re-download on next access)."""
    _CACHE.clear()
    print("[BlobLoader] Cache cleared.")


def preload_all():
    """
    Pre-download all knowledge blobs at startup.
    Call this once in app.py or orchestrator.py for faster first requests.
    """
    blobs = [
        "additives.json",
        "dietary_limits.json",
        "drug_food_interactions.json",
        "glycemic_index.json",
        "iarc_carcinogens.json",
        "nova_classification.json",
    ]
    for name in blobs:
        load_knowledge_blob(name, fallback={})
    print("[BlobLoader] All knowledge blobs preloaded.")
