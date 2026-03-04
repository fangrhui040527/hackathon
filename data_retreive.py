"""
data_retreive.py
Handles uploading food analysis JSON to Azure Blob Storage
and retrieving it back for the agents to consume.

When Azure Blob Storage is not configured, operations are skipped gracefully.
"""

import os
import json
import uuid
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "food-analysis")


def _is_blob_configured() -> bool:
    """Check if Azure Blob Storage is configured."""
    return bool(CONNECTION_STRING)


def _get_container_client():
    """Get or create the blob container client."""
    if not CONNECTION_STRING:
        raise ValueError(
            "AZURE_STORAGE_CONNECTION_STRING is not set in .env — "
            "cannot connect to Blob Storage."
        )
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        raise ImportError(
            "azure-storage-blob package is not installed. "
            "Install it with: pip install azure-storage-blob"
        )
    blob_service = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_service.get_container_client(CONTAINER_NAME)
    try:
        container_client.create_container()
    except Exception:
        pass  # Container already exists
    return container_client


def upload_to_blob(data: dict, blob_name: Optional[str] = None) -> str:
    """
    Upload a dict as JSON to Azure Blob Storage.

    Args:
        data: The food analysis data to store.
        blob_name: Optional blob name. Auto-generated if not provided.

    Returns:
        The blob name used for storage (needed for retrieval).
    """
    if blob_name is None:
        blob_name = f"food_analysis_{uuid.uuid4().hex[:8]}.json"

    container_client = _get_container_client()
    blob_client = container_client.get_blob_client(blob_name)
    from azure.storage.blob import ContentSettings
    blob_client.upload_blob(
        json.dumps(data, indent=2, ensure_ascii=False),
        overwrite=True,
        content_settings=ContentSettings(content_type="application/json"),
    )
    return blob_name


def retrieve_from_blob(blob_name: str) -> dict:
    """
    Retrieve and parse a JSON blob from Azure Blob Storage.

    Args:
        blob_name: The name of the blob to retrieve.

    Returns:
        Parsed dict of the food analysis data.
    """
    container_client = _get_container_client()
    blob_client = container_client.get_blob_client(blob_name)
    blob_data = blob_client.download_blob().readall()
    return json.loads(blob_data)


def list_blobs(prefix: str = "food_analysis_") -> list[str]:
    """List all food analysis blobs in the container."""
    container_client = _get_container_client()
    return [b.name for b in container_client.list_blobs(name_starts_with=prefix)]
