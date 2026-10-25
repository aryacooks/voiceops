# Evaluation summary

Questions: 52. Retrieval: multilingual-e5-base + BM25 RRF (+ LLM query rewrite when enabled), top five. Full LLM evaluation enabled: True.

| Stage | LLM items scored | Correctness | Evidence recall@5 (macro) | Unanswerable IDK accuracy |
| --- | ---: | ---: | ---: | ---: |
| step1 | 52 | 0.058 | 0.000 | 0.800 |
| step2 | 52 | 0.788 | 0.770 | 0.400 |
| step3 | 52 | 0.904 | 0.858 | 0.400 |

Recall is the fraction of gold section/catalog IDs in the retrieved five, macro-averaged over rows with gold evidence. Baseline has no retrieved evidence by design. Retrieval numbers are not answer correctness. No answer/judge calls run when credentials are absent.

Conversation evaluation is a separate command. Its missing scores must not be inferred from retrieval results.
