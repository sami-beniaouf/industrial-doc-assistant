"""First test: turn sentences into vectors and compare how close they are.

Run from the repository root:  python scripts/check_embedding.py
"""
import sys
from pathlib import Path

import numpy as np
from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docassistant.config import settings  # noqa: E402

client = AzureOpenAI(
    azure_endpoint=settings.openai_endpoint,
    api_key=settings.openai_api_key,
    api_version=settings.openai_api_version,
)

question = "Comment régler la vitesse de la fraiseuse ?"
passages = [
    "Ajuster la fréquence de rotation de la broche selon le matériau usiné.",
    "Porter des lunettes de protection lors du travail à la meuleuse.",
    "La cafétéria est ouverte de 11h30 à 13h30.",
]

response = client.embeddings.create(model=settings.embedding_deployment, input=[question, *passages])
vectors = [np.array(item.embedding) for item in response.data]

print(f"Vector size: {len(vectors[0])} numbers per text")
print(f"Tokens used: {response.usage.total_tokens}\n")
print(f"Question: {question}\n")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


for passage, vector in zip(passages, vectors[1:]):
    print(f"{cosine(vectors[0], vector):.3f}  {passage}")
