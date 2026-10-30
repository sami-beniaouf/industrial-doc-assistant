"""Shared Azure clients."""
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import AzureOpenAI

from .config import settings


def openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=settings.openai_endpoint,
        api_key=settings.openai_api_key,
        api_version=settings.openai_api_version,
    )


def _search_credential() -> AzureKeyCredential:
    if not settings.search_endpoint or not settings.search_api_key:
        raise RuntimeError("Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY in .env")
    return AzureKeyCredential(settings.search_api_key)


def search_index_client() -> SearchIndexClient:
    return SearchIndexClient(settings.search_endpoint, _search_credential())


def search_client() -> SearchClient:
    return SearchClient(settings.search_endpoint, settings.search_index, _search_credential())
