# Evaluation set

`questions.json` holds 26 French questions about the Suva documents:

| Category | n | What it tests |
|---|---|---|
| `fact` | 6 | precise values in machine sheets |
| `paraphrase` | 5 | questions reworded away from the document's vocabulary |
| `standard` | 4 | exact standard numbers |
| `method` | 4 | the risk assessment method |
| `multi` | 3 | answers spread over several passages |
| `trap`, `out_of_scope` | 4 | the assistant must refuse (`expected_behavior: refuse`) |

The questions were drafted with an AI assistant from the documents and selected by the author. Each expected answer and expected page was checked automatically against the PDF text.

## Corrections after the first run

After reading the first results, four entries were corrected because the expected data was wrong or too strict, not the assistant:

- **#7**: the expected answer said "no", but the document allows music in some cases; it now states only the hearing-protection rule.
- **#16**: page 43 lists the three steps in one sentence; pages 43 and 47 were added to the expected pages.
- **#17**, **#19**: the expected answers contained details the question did not ask for.

## Running

```powershell
python scripts/evaluate.py --runs 3
```

Retrieval is almost deterministic (the vector search is approximate and can vary slightly between runs); generation and judging are not, hence several runs. Retrieval metrics are computed on the first run. The judge is the same chat model that answers, which is a limitation: failures are reviewed by hand.
