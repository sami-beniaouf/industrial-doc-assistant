"""Test configuration: dummy settings, so importing the package never needs real Azure credentials."""
import os

os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://example.invalid")
os.environ.setdefault("AZURE_OPENAI_API_KEY", "test-key")
