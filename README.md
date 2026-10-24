# ZentroMart VoiceOps 2026

A four-stage synthetic customer-support capstone: prompt-only baseline, cited hybrid RAG, verified conversational tools, and Gnani speech. The grading CLI and demo share the same agent. The frozen reference date is **20 October 2026**.

**Status:** complete and evaluated live (24 October 2026) with Gnani STT/TTS and `openai/gpt-6-luna` via OpenRouter. Public GitHub URL: **https://github.com/aryacooks/voiceops**.

## Results

| Practice questions (52, noisy ASR text) | Step 1 prompt-only | Step 2 RAG | Step 3 agent (`run.py`) |
| --- | ---: | ---: | ---: |
| Correct answers (LLM judge) | 5.8% | 76.9% | **90.4%** |
| Evidence recall@5 | – | 0.745 | **0.904** |
| "I don't know" on unanswerable | 60% | 60% | **100%** |

Practice conversations (23 sessions, 96 turns): 81.3% of turns fully correct, 92.7% correct decision, 98.1% expected tool calls. Full per-item results are in `eval/results/`; method, failures and fixes are in `report.pdf`.

## Setup (Python 3.11)

```sh
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# macOS
brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
cp .env.example .env
```

Extract `Capstone_Project_Dataset_FTTT_2026.zip` so `dataset/kb`, `dataset/data`, `dataset/practice` and `dataset/tools` exist. Dataset contents, `.env`, indexes and `.venv` are ignored. Use only the supplied synthetic dataset. Then:

```sh
python dataset/validate_dataset.py
python build_index.py
pytest -q
```

The first index build downloads the public `intfloat/multilingual-e5-base` model (~1.1 GB, multilingual so Hindi/Hinglish questions match English policy) from Hugging Face; no API key is needed. Later use relies on the local model cache. `run.py` builds the index automatically if absent, incomplete or inconsistent with the dataset. The index stores dense numpy vectors and JSON metadata, not a remote vector database. Retrieval fuses dense cosine and BM25 (reciprocal rank fusion) over the raw transcript plus an LLM-rewritten English query (`QUERY_REWRITE=0` disables it), then applies policy precedence; superseded policies remain indexed with a strong penalty. Public catalog rows are included for SKU facts. Support logs are excluded.

## Configuration

Set these environment variables in `.env` (never commit it):

| Variable | Meaning/default |
| --- | --- |
| `GNANI_API_KEY` | Gnani speech API key; required only for audio |
| `LLM_BASE_URL` | OpenAI-compatible endpoint, e.g. `https://openrouter.ai/api/v1` (used for the reported results) or `https://api.openai.com/v1` |
| `LLM_API_KEY` | Provider key; local Ollama can use the provider's placeholder value |
| `LLM_MODEL` | Exact provider model ID, e.g. `openai/gpt-6-luna` on OpenRouter; must support tool calling |
| `LLM_API_MODE` | `chat` for OpenRouter; `auto` (bare GPT-6 IDs use Responses, others Chat Completions) or `responses` |
| `DATASET_DIR` | `./dataset` |
| `INDEX_DIR` | `./index` |
| `STT_LANG` | `en-IN` (configurable Indian locale) |
| `TTS_LANG` | `en-IN`; set `hi-IN`/`hi-en` when appropriate |
| `TTS_VOICE` | `Kaveri`; use a voice suitable for the configured language/model |
| `TTS_MODEL` | `timbre-v2.5`, always explicitly sent |
| `QUERY_REWRITE` | `1` (default) rewrites each query into English with the LLM before retrieval; `0` disables |
| `EMBED_MODEL` | `intfloat/multilingual-e5-base` |

The OpenAI SDK handles both native function-call APIs. Temperature 0 is sent except to GPT-6 reasoning models, which reject it. Other OpenAI-compatible providers must support native tools. No secret is inferred from existing app login sessions.

## Grading command

```sh
python run.py --input path/to/audio --output outputs/
```

Processes `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`. Files named `<conversation>_turn<N>` or `<conversation>_<N>` share an Agent and run in numeric turn order; other files have fresh sessions. File iteration is sorted by session, numeric turn, filename. Mixed encodings with the same stem get unique names to avoid overwrites. Supported inputs are directly inside the input folder.

Each file produces `<name>.json`, and successful Gnani TTS produces `<name>.reply.wav`. JSON includes transcript (verification proof redacted), reply text, speech-normalized text, retrieved evidence, citations, redacted tool audit and latency. `results.jsonl` and `results.csv` summarize every input. A failed file is recorded and processing continues; a nonzero exit code signals any errors. No silent WAV is fabricated when speech fails. TTS failures retain the text response. STT failures retain an error record.

For text-only runs, without Gnani calls:

```sh
python run.py --text-mode dataset/practice/questions.csv --output outputs/text/
python run.py --text-mode dataset/practice/conversations.csv --output outputs/conversations/
```

Text CSVs use `asr_text`, or `customer_message` for conversation CSVs, and optionally `conversation_id` and `turn`. Text mode never creates audio. The CLI exits 1 when credentials are missing, while writing per-input error artifacts.

## Demo and evaluation

```sh
python app.py
python eval/eval_questions.py --retrieval-only
python eval/eval_questions.py
python eval/eval_conversations.py
```

The local Gradio app has a microphone/upload path, typed follow-ups, persistent session, evidence inspection and redacted tool audit. Typed text takes precedence over stale uploaded audio. **Inspect retrieval only** works without an LLM key and displays source chunks; it does not generate an answer. New conversation clears session and all outputs.

Question evaluation uses all 52 noisy `asr_text` prompts, logs Step 1 vs Step 2 separately, computes macro evidence recall@5, and uses an LLM judge for correctness and insufficient-evidence behavior on unanswerable items. Native-script/spoken/date equivalence is judged semantically. Conversation evaluation replays 96 turns in 23 sessions, judges decisions and checks expected tool names/arguments using ephemeral raw arguments (proof never exported). Expected leading-zero proof values stay strings. Gold labels are read only by the evaluation scripts, never by the runtime agent.

When no keys exist, retrieval scores still run and answer/judge scores are explicitly null/not run. `eval/results/summary.md` and `conversation_summary.json` record that distinction. LLM judging is model-dependent and should be checked manually on failures; retrieval recall does not establish answer correctness.

## Verification and limitations

Order details are exposed only through the supplied identity-gated tool. The adapter accepts only caller-provided proof and limits failure to two distinct caller turns per order; repeated tool calls within a turn reuse results. The full order payload remains session-private. Public audits omit it and redact submitted verification values. The mock check is a teaching simulation, not production authentication.

Every turn retrieves evidence before policy generation, with additional native `search_kb`, verified `lookup_order`, `create_ticket`, `date_calc`, catalog and pincode tools. Date arithmetic excludes start dates, Sundays and supplied holidays for business days; calendar return windows remain separate. No refund, cancellation, credit or pickup mutation tool exists. First-person claims of actions no tool performs are removed in English/Hindi/Hinglish (policy explanations are kept), sentences resting only on invented citations are dropped, and confirmed tickets always carry their real ID. These guards supplement prompts but are not a proof of semantic correctness; live adversarial multilingual review remains necessary.

The running summary stores redacted older user/assistant turns with a 2,400-character budget, alongside the last 12 turns and explicit slots. Only current session data supplies verification proof. Speech clips are converted to 16 kHz mono 16-bit WAV and split at nearby silence, bounded at 55 seconds each. Gnani requests retry transient errors; authentication/invalid-request errors fail immediately. Speech normalization removes citations/Markdown, expands dates with year, reads IDs in groups, and says rupees.

## Report and submission

The report source is `report/report.md`. Rebuild the PDF with the parent-provided script:

```sh
uv run --with reportlab --with pypdf scripts/build_report.py
python scripts/package_submission.py
```

The submission script refuses a final package until `demo.mp4` and Gnani sample artifacts exist. For an explicitly incomplete source bundle:

```sh
python scripts/package_submission.py --allow-incomplete --output voiceops_source.zip
```

Final `team_name_voiceops.zip` must include README, `.env.example`, requirements, entry points, `src/`, `eval/`, report PDF, a real two-minute `demo.mp4` and real `sample_outputs/`. Exclude `.env`, keys, `.venv`, dataset and its archive. Record the demo with one cited policy answer, a follow-up, then a handover/unknown answer. See `sample_outputs/README.md` for recording steps.

Official integration references: [Gnani SDK STT](https://docs.gnani.ai/python-sdk/speech-to-text), [SDK TTS](https://docs.gnani.ai/python-sdk/text-to-speech), [Quick Start](https://docs.gnani.ai/api/introduction/quick-start), [STT REST](https://docs.gnani.ai/api/STT/speech-to-text), [TTS REST](https://docs.gnani.ai/api/TTS/tts-inference), [voice catalog](https://docs.gnani.ai/api/TTS/available-voices), [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling). Checked 23 October 2026.
