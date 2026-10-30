"""Second test: ask the chat model to answer ONLY from a given passage.

This is the core idea of RAG (retrieval-augmented generation): the model does not
answer from memory, it answers from the text we retrieved for it.

Run from the repository root:  python scripts/check_chat.py
"""
import sys
from pathlib import Path

from openai import AzureOpenAI

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from docassistant.config import settings  # noqa: E402

client = AzureOpenAI(
    azure_endpoint=settings.openai_endpoint,
    api_key=settings.openai_api_key,
    api_version=settings.openai_api_version,
)

passage = (
    "[Source: Fiche machine F-12, page 3] Avant tout réglage de la fréquence de rotation "
    "de la broche, arrêter la fraiseuse et attendre l'immobilisation complète de l'outil. "
    "La vitesse se règle avec le sélecteur situé sur le côté gauche du bâti."
)

system_prompt = (
    "Tu es un assistant documentaire pour un atelier industriel. "
    "Réponds uniquement à partir des extraits fournis. "
    "Cite la source entre crochets. "
    "Si l'information n'est pas dans les extraits, réponds : "
    "« Je ne trouve pas cette information dans les documents. »"
)

for question in [
    "Comment régler la vitesse de la fraiseuse ?",
    "Quelle est la puissance du moteur de la fraiseuse ?",
]:
    response = client.chat.completions.create(
        model=settings.chat_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extraits :\n{passage}\n\nQuestion : {question}"},
        ],
    )
    print(f"Q: {question}")
    print(f"R: {response.choices[0].message.content}")
    print(f"   ({response.usage.total_tokens} tokens)\n")
