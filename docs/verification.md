# Verification - 24 October 2026

- Dataset validator: PASS (9 CSVs, 21 KB documents, 52 questions, 23 conversations / 96 turns).
- Test suite: **48 passed** (dates, caller verification and retries, redaction, action/ticket/citation guards, session memory, batching, speech formatting).
- Live LLM: `openai/gpt-6-luna` via OpenRouter, chat completions with native tool calls. Total evaluation spend about USD 0.57.
- Live Gnani: TTS (`timbre-v2.5`, Kaveri) and STT (`en-IN`) round trip verified; `run.py` processed all 6 sample clips with 0 errors (`sample_outputs/`).
- Question eval (`eval/results/summary.md`): Step 1 5.8%, Step 2 76.9%, Step 3 agent 90.4% correct; agent evidence recall@5 0.904.
- Conversation eval (`eval/results/conversation_summary.json`): 81.3% turns correct, 92.7% decisions, 98.1% expected tool calls.
- Retrieval without the LLM rewrite, raw ASR text: 0.649 recall@5. An earlier 0.926 relied on a phrase list copied from the practice questions; it was removed because it would not transfer to unseen test questions.

Not verified here: the two-minute demo video (needs a screen recording by the author) and audio from real human callers (sample inputs were generated with Gnani voices).
