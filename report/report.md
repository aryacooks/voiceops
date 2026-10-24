# ZentroMart VoiceOps 2026

## Summary

A voice customer-support agent for ZentroMart, built in four stages that share one Python codebase: a prompt-only baseline, cited RAG, a multi-turn agent with verified tools, and Gnani speech in and out. All numbers below come from live runs on 24 October 2026 with `openai/gpt-6-luna` (via OpenRouter) and Gnani STT/TTS. Answers are scored by an LLM judge against each practice item's expected decision, required facts and forbidden claims. "Today" is fixed at 20 October 2026.

| Practice questions (52, noisy `asr_text`) | Step 1 prompt-only | Step 2 RAG | Step 3 agent (used by `run.py`) |
| --- | ---: | ---: | ---: |
| Correct answers | 5.8% (3/52) | 76.9% (40/52) | **90.4% (47/52)** |
| Evidence recall@5 (gold section IDs retrieved) | – | 0.745 | **0.904** |
| Says "I don't know" on unanswerable items | 60% | 60% | **100%** |

| Practice conversations (23 sessions, 96 turns) | Score |
| --- | ---: |
| Turns judged fully correct | 81.3% (78/96) |
| Correct decision (answer / clarify / refuse / escalate) | 92.7% |
| Expected tool calls made with the right arguments | 98.1% |
| Gold evidence retrieved | 88.9% |

## Architecture

```text
audio file / Gradio mic
  -> pydub: mono 16 kHz WAV, split near silence into <=55 s clips
  -> Gnani STT (en-IN, accepts Hinglish)
  -> Agent (one per session)
       LLM query rewrite -> multilingual-e5 dense + BM25 -> RRF -> policy precedence
       tools: search_kb, lookup_order (verified), create_ticket, date_calc, catalog
       reply guard: citations, unsupported-action and ticket checks
  -> speech normalisation (dates with year, rupees, grouped IDs, short ticket refs)
  -> Gnani TTS (timbre-v2.5, Kaveri)
```

`python run.py --input AUDIO_DIR --output OUT_DIR` is the grading command. Files named `<conv>_turnN` share one session; other files each get a fresh session. For every input it writes a JSON file (transcript, reply, spoken text, retrieved chunks, cited IDs, tool audit, latency) and the reply WAV, plus `results.jsonl` and `results.csv` for the batch. A failure on one file is recorded and the batch continues.

## What was built in each step

**Step 1: prompt only.** A system prompt sets the role (ZentroMart's AI support assistant, introduced in the first reply), the limits (no invented policy, amounts or dates) and the fixed date. With no documents it scored 5.8%. It mostly, and correctly, declined to guess. That is the point of the baseline: the model does not know ZentroMart's policies.

**Step 2: RAG.** The 21 KB files are split into 84 chunks, one per `[SECTION-ID]`, keeping the doc type, status, version and `effective_from` date. The 70 catalog rows are added so a product's return category, seller and warranty can be cited. Retrieval:

- **Multilingual embeddings.** An English-only model (`bge-small-en`) reached only 0.14 recall on Hindi questions. `multilingual-e5-base` reached 0.67. On overall dense recall it tied `bge-m3` (0.638) at half the size and beat `e5-small` (0.596).
- **Hybrid search.** BM25 is fused with dense search by reciprocal rank fusion, at half weight because it over-matches the Hindi FAQ.
- **LLM query rewrite.** Noisy, Hindi or Hinglish ASR text is rewritten into one English search query and fused with the raw text, which keeps exact names and SKUs. This lifted recall from 0.649 to 0.745.
- **Catalog-aware routing.** When a product is named, its catalog facts become an extra query, so the policy for that category (e.g. the fashion return window) is found. Spoken SKUs and years are normalised ("ele zero zero one two" → ELE-0012, "two zero two six" → 2026).
- **KB-00 rules.** Results follow the precedence order: current policy > agent guide > help > FAQ > marketing. A superseded section is kept only when its current successor refers to that version (returns v3 for electronics delivered before 1 August 2026). The KB-00 calendar or precedence rule is attached when a retrieved chunk depends on it.

The answer prompt allows only cited evidence and has a deterministic `date_calc` tool for business-day maths. If the evidence doesn't cover the question, the reply says so and offers a human colleague.

**Step 3: conversation.** The agent keeps the last 12 turns, a running summary, the current order ID, the verification status, and the verified order record with phone, email, address and pincode removed. The three KB agent guides (style, escalation, verification) are loaded into the system prompt every turn. The code enforces several rules:

- **Caller verification.** `lookup_order` only runs with an order ID and proof the caller actually said, and allows one retry. Proof values are redacted from logs.
- **Tickets.** A handover is confirmed only when `create_ticket` returns `created=True`, and always with the real ID.
- **Unsupported actions.** Sentences claiming an action no tool can do ("I've refunded / cancelled") are removed, but policy explanations ("your refund will be processed within…") are kept.
- **Citations.** Sentences resting only on invented citations are dropped. Stated facts with no source become "I don't know".

**Step 4: voice.** The voice layer uses only the official `gnani-vachana` SDK clients. It always names the TTS model (`timbre-v2.5`), keeps each STT clip under 60 s, retries temporary errors, and replies "Sorry, I didn't catch that" to empty or noise-only transcripts. Replies are rewritten for listening: citations and markdown removed, years added to dates, rupee amounts read as "rupees", order IDs grouped, and 35-character ticket IDs shortened to "ticket ending in 0 6 8 4". `sample_outputs/` holds a live 3-turn call (cancel request → verification → Rs 500 demand refused and handed over) and three single questions, including Hindi and one the KB doesn't cover. A Gradio app (`app.py`) records from the microphone and shows the transcript, reply audio, sources and tool audit. It is used to record the demo video.

## Step 1 vs Step 2, and what we learned

RAG lifted correctness from 5.8% to 76.9%. The full agent reached 90.4%, because it can search again with its own queries, compute dates and use tools. Building the evaluation exposed several problems:

- **A misleading early retrieval score.** A first version reported 0.926 recall, but it used a phrase list copied from the practice questions. Without that list the same retriever scored 0.645. We removed it and report only general methods. The test set uses unseen questions, so a tuned list would not have carried over.
- **An over-eager action guard.** It deleted correct refund-timeline answers ("your refund will be processed in 5–7 business days") as false action claims, and replaced plain clarifying questions with "I don't know". Narrowing it to first-person completion claims fixed both.
- **Lost order memory.** The verified record lived only inside the verification turn, so later turns said "shipped date unavailable". Keeping it in session context lifted conversation correctness from 72% to 80%.
- **Citations of agent guides were treated as invented.** A sentence citing [ESC-2] was dropped, and the ticket ID went with it. Guide sections now count as evidence, and the confirmed ticket ID is attached after filtering.
- **An unfair judge.** At first the judge couldn't see tool results, so it scored grounded order facts and real ticket IDs as invented. It now receives the verified record, the created tickets and the cited text.

## Remaining weaknesses and next steps

- **Turn after verification.** Some sessions expect the agent to address an issue the customer never actually stated. The agent now summarises the order's key status first, but a few such turns still fail.
- **Required details.** The agent sometimes leaves out a required detail, for example "parcel refused, so the refund comes in 7 days", or names the right team but not the exact "Priority Resolution" label.
- **Date edge cases.** Return deadlines that depend on two rules at once (a festive-sale order plus the delivery date) are occasionally off by one day. A dedicated `return_deadline(order)` tool would make this exact.
- **Hindi speech recognition.** STT uses `en-IN`, which handles English and Hinglish well. Pure Hindi audio was sometimes truncated. Next we would detect the language per clip and pass `hi-IN`.
- **Evaluation limits.** The judge is the same model family as the agent. A second judge model, and native-speaker review of the Hindi replies, would make the scores more reliable.

**Bonus work:** hybrid multilingual retrieval with a measured model comparison; LLM query rewriting; a deterministic business-day calculator honouring `holidays.csv`; catalog-aware policy routing; privacy redaction of caller proof; a reply guard against false actions and tickets; and a 48-test suite covering dates, verification, guards, batching and speech formatting.
