"""Answer generation: the chat model answers only from the retrieved passages."""
from dataclasses import dataclass

from .clients import openai_client
from .config import settings
from .search import Passage, retrieve

NOT_FOUND = "Je ne trouve pas cette information dans les documents."

SYSTEM_PROMPT = (
    "Tu es un assistant documentaire pour un atelier industriel (sécurité et qualité). "
    "Réponds en français, uniquement à partir des extraits fournis, "
    "sans utiliser tes connaissances générales. "
    "Après chaque affirmation, cite sa source entre crochets au format [document, p. page], "
    "en reprenant exactement les références des extraits. "
    "Pour une question fermée (oui/non), commence par « Oui » ou « Non », puis justifie avec l'extrait : "
    "une interdiction explicite (« ne jamais », « interdit ») répond « Non », "
    "une obligation explicite (« il faut », « porter ») répond « Oui ». "
    "Réponds dès qu'un extrait traite explicitement le sujet de la question (même machine, même équipement) ; "
    "ne déduis rien d'un extrait qui concerne une autre machine ou un autre sujet. "
    f"Si aucun extrait ne répond à la question, réponds exactement : « {NOT_FOUND} » "
    "et rien d'autre."
)


@dataclass(frozen=True)
class Answer:
    question: str
    text: str
    passages: list[Passage]
    total_tokens: int


def format_context(passages: list[Passage]) -> str:
    return "\n\n".join(f"[{p.source}, p. {p.page}]\n{p.content}" for p in passages)


def answer(question: str, top: int = 5, mode: str = "hybrid") -> Answer:
    passages = retrieve(question, top=top, mode=mode)
    response = openai_client().chat.completions.create(
        model=settings.chat_deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extraits :\n{format_context(passages)}\n\nQuestion : {question}"},
        ],
    )
    return Answer(question, response.choices[0].message.content, passages, response.usage.total_tokens)
