"""Architecture diagram of the README: docs/architecture.svg."""
from svglib import LINE, MUTED, Svg

W, M = 1240, 16
s = Svg(W)

# geometry
LX, LW = 16, 190                    # left column: documents and interface
AX, AW = 320, 220                   # application column (Python)
AR = AX + AW
ROW1, BH1 = 84, 130                 # ingestion row
ROW2, BH2 = 500, 140                # question row
FZ_X, FZ_Y, FZ_W, FZ_H = 300, 250, 510, 190        # Microsoft Foundry zone
EMB_X, CHAT_X, MW, MY, MH = 320, 570, 220, 292, 130  # model boxes
SZ_X, SZ_Y, SZ_W, SZ_H = 900, 70, 300, 590         # Azure AI Search zone
SB_X, SB_W = 920, 260
MODELS_BOTTOM = MY + MH

s.t(M, 62, "INGESTION · RUN ONCE", 13, "bold", MUTED, "start")
s.t(M, 484, "QUESTION · EVERY REQUEST", 13, "bold", MUTED, "start")

# Azure zones
s.zone(FZ_X, FZ_Y, FZ_W, FZ_H, "#f7faff", "#bcd6f2", "Microsoft Foundry", "#0b5cad", icon="foundry")
s.zone(SZ_X, SZ_Y, SZ_W, SZ_H, "#f7faff", "#bcd6f2", "Azure AI Search", "#0b5cad", icon="search")

# ingestion row
s.box(LX, ROW1, LW, BH1, "Suva documents", ["6 public PDFs, French", "about 30,000 words"], "white", icon="pdf")
s.box(AX, ROW1, AW, BH1, "Ingestion script", ["extract and clean text", "300-word chunks,", "50-word overlap"], "white", icon="python")
s.box(SB_X, 112, SB_W, BH1, "Search index", ["industrial-docs", "168 chunks: text + vector"], "white", icon="search")

# models
s.box(EMB_X, MY, MW, MH, "Embeddings", ["text-embedding-3-small", "1536 dimensions"], "white", icon="openai")
s.box(CHAT_X, MY, MW, MH, "Chat model", ["gpt-5.4-mini", "Data Zone, processed in Europe"], "white", icon="openai")

# question row
s.box(LX, ROW2, LW, BH2, "Streamlit interface", ["question, answer,", "sources, thumbs up/down"], "white", icon="streamlit")
s.box(AX, ROW2, AW, BH2, "Retrieval and answer", ["Python: retrieve(), answer()", "citations, query log"], "white", icon="python")
s.box(SB_X, ROW2, SB_W, BH2, "Hybrid search", ["keywords + vectors,", "fused by RRF", "top 5 passages"], "white", icon="search")

# ingestion flow
s.arrow([(LX + LW, 149), (AX - 4, 149)])
s.t((LX + LW + AX) / 2, 141, "read pages", 12.5)
s.arrow([(500, ROW1 + BH1), (500, MY - 4)])
s.t(492, 236, "1 · embed chunks", 12.5, anchor="end")
s.arrow([(AR, 149), (SB_X - 4, 149)])
s.t((AR + SB_X) / 2, 141, "2 · upload chunks and vectors", 12.5)

# question flow
s.arrow([(LX + LW, 540), (AX - 4, 540)])
s.t((LX + LW + AX) / 2, 532, "question", 12.5)
s.arrow([(AX, 600), (LX + LW + 4, 600)])
s.t((LX + LW + AX) / 2, 617, "answer, sources", 12.5)
s.arrow([(500, ROW2), (500, MODELS_BOTTOM + 4)])
s.t(492, 472, "1 · embed question", 12.5, anchor="end")
s.arrow([(AR, 575), (SB_X - 4, 575)])
s.t((AR + SB_X) / 2, 566, "2 · hybrid search", 12.5)
s.arrow([(SB_X, 615), (AR + 4, 615)])
s.t((AR + SB_X) / 2, 633, "top 5 passages", 12.5)
s.arrow([(AR, 540), (680, 540), (680, MODELS_BOTTOM + 4)])
s.t(688, 470, "3 · question + passages", 12.5, anchor="start")
s.arrow([(600, MODELS_BOTTOM), (600, 516), (AR + 4, 516)])
s.t(608, 500, "answer", 12.5, anchor="start")
s.arrow([(1050, 112 + BH1 + 4), (1050, ROW2 - 4)], color=LINE, dash="6 5")
s.t(1058, 370, "same index", 12.5, anchor="start")

# across the project
BY = 700
s.t(M, BY, "ACROSS THE PROJECT", 13, "bold", MUTED, "start")
cards = [("Evaluation", ["31 questions, 3 runs: retrieval,", "answers, refusals, citations"]),
         ("Tests and CI", ["GitHub Actions: ruff and pytest", "on every push, no Azure access"]),
         ("Secrets", ["Keys in .env, ignored by Git;", "keyless authentication planned"]),
         ("Observability", ["JSONL query log: latency, tokens,", "retrieved and cited pages, feedback"])]
CW = (W - 2 * M - 3 * 24) / 4
for k, (title, lines) in enumerate(cards):
    s.box(M + k * (CW + 24), BY + 18, CW, 100, title, lines, "white")

LY = 872
s.line(M, LY - 26, W - M, LY - 26)
s.arrow([(M, LY - 4), (M + 34, LY - 4)])
s.t(M + 44, LY, "data flow", 12.5, anchor="start")
s.t(M + 140, LY, "Steps 1-2 run once at ingestion; steps 1-3 run for every question", 12.5, anchor="start")
s.save("architecture.svg", LY + 24, "Architecture of the industrial document assistant")
