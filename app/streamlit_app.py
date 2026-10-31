"""Streamlit interface: ask a question, read the answer and check its sources.

Run from the repository root:  streamlit run app/streamlit_app.py
"""
import sys
import time
from pathlib import Path
from uuid import uuid4

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

st.set_page_config(page_title="Assistant sécurité et qualité en atelier")

try:
    from docassistant.answer import NOT_FOUND, answer
    from docassistant.evaluation import is_refusal, parse_citations
    from docassistant.query_log import log_event
    from docassistant.search import MODES
except RuntimeError as error:  # a required environment variable is missing (see .env.example)
    st.error(f"Configuration manquante : {error}")
    st.stop()

EXAMPLES = [
    "Quelle norme s'applique aux machines à meuler fixes ?",
    "Quelles sont les règles de sécurité pour la meuleuse d'angle ?",
    "Faut-il porter des gants sur une fraiseuse conventionnelle ?",
    "Quelles sont les trois étapes de la méthode de réduction des risques ?",
]



def save_feedback(query_id: str, key: str) -> None:
    rating = st.session_state.get(key)  # st.feedback("thumbs"): 1 = up, 0 = down, None = cleared
    if rating is not None:
        log_event({"type": "feedback", "query_id": query_id, "rating": "up" if rating == 1 else "down"})


PREVIEW_CHARS = 200  # characters of each passage shown in the sources panel


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Paramètres")
    mode = st.selectbox(
        "Mode de recherche", MODES, index=0,
        help="hybrid : mots-clés + vecteurs (recommandé). keyword : mots-clés seuls. vector : vecteurs seuls.",
    )
    top = st.slider("Nombre de passages", min_value=3, max_value=10, value=5,
                    help="Passages envoyés au modèle. Plus de passages aident pour les questions « liste », mais ajoutent du bruit.")
    st.subheader("Exemples")
    for example in EXAMPLES:
        if st.button(example, use_container_width=True):
            st.session_state.pending = example
    if st.button("Effacer la conversation"):
        st.session_state.messages = []
        st.rerun()

st.title("Assistant sécurité et qualité en atelier")
st.caption(
    "Réponses fondées uniquement sur des documents Suva, avec leurs sources (document et page du PDF). "
    "Chaque question est traitée séparément : l'assistant ne garde pas le fil de la conversation."
)


def render(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["text"])
            return
        if message["refused"]:
            st.info(message["text"])
        else:
            st.markdown(message["text"])
        key = f"feedback_{message['id']}"
        st.feedback("thumbs", key=key, on_change=save_feedback, args=(message["id"], key))
        n = len(message["passages"])
        title = f"Passages consultés ({n}), aucun ne répond à la question" if message["refused"] else f"Sources ({n} passages récupérés)"
        with st.expander(title):
            for p in message["passages"]:
                label = f"**{p['source']}**, page {p['page']}" + (" (citée dans la réponse)" if p["cited"] else "")
                st.markdown(label)
                st.caption(p["content"][:PREVIEW_CHARS] + ("…" if len(p["content"]) > PREVIEW_CHARS else ""))
        st.caption(f"Mode : {message['mode']} · {message['tokens']} tokens")


question = st.chat_input("Pose ta question sur la sécurité en atelier") or st.session_state.pop("pending", None)

for message in st.session_state.messages:
    render(message)

if question:
    user_message = {"role": "user", "text": question}
    st.session_state.messages.append(user_message)
    render(user_message)

    query_id = uuid4().hex[:8]
    started = time.perf_counter()
    with st.spinner("Recherche dans les documents…"):
        try:
            result = answer(question, top=top, mode=mode)
        except Exception as error:  # network, quota, authentication...
            log_event({"type": "error", "id": query_id, "question": question, "mode": mode, "error": type(error).__name__})
            st.error(f"L'appel à Azure a échoué ({type(error).__name__}). Détails dans le terminal.")
            raise
    latency = time.perf_counter() - started

    cited = parse_citations(result.text)
    refused = is_refusal(result.text, NOT_FOUND)
    assistant_message = {
        "id": query_id,
        "role": "assistant",
        "text": result.text,
        "refused": refused,
        "mode": mode,
        "tokens": result.total_tokens,
        "passages": [
            {"source": p.source, "page": p.page, "content": p.content, "cited": (p.source, p.page) in cited}
            for p in result.passages
        ],
    }
    log_event({
        "type": "query", "id": query_id, "question": question, "mode": mode, "top": top,
        "answer": result.text, "refused": refused,
        "retrieved": [[p.source, p.page] for p in result.passages],
        "cited": sorted([list(c) for c in cited]),
        "tokens": result.total_tokens, "latency_s": round(latency, 2),
    })
    st.session_state.messages.append(assistant_message)
    render(assistant_message)
