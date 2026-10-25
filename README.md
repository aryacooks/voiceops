# ZentroMart VoiceOps

A voice support agent for a synthetic store. It listens (Gnani STT), answers from the policy documents with citations, checks orders after verifying the caller, hands over to a human when policy requires, and speaks the reply (Gnani TTS). "Today" is fixed at 20 October 2026.

**Live demo:** https://aryabysani--voiceops-web.us-east.modal.run (first load can take a minute)

## Results

| 52 practice questions | Step 1 prompt only | Step 2 RAG | Step 3 agent |
| --- | ---: | ---: | ---: |
| Correct | 5.8% | 76.9% | **90.4%** |
| Evidence recall@5 | – | 0.745 | **0.904** |
| "I don't know" when unanswerable | 60% | 60% | **100%** |

23 practice conversations: 92.7% correct decisions, 98.1% expected tool calls. Details in `report.pdf` and `eval/results/`.

## Setup

Python 3.11 and ffmpeg (`brew install ffmpeg` or `apt-get install ffmpeg`).

```sh
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your keys
python build_index.py
```

Put the dataset at `./dataset` (or set `DATASET_DIR`). `run.py` builds the index itself if it is missing.

## Run

```sh
python run.py --input path/to/audio --output outputs/
```

- Reads `.wav .mp3 .m4a .flac .ogg`.
- Files named `<conv>_turn<N>` or `<conv>_<N>` are one conversation, in turn order. Any other file is its own session.
- Writes `<name>.reply.wav` and `<name>.json` per file, plus `results.jsonl` and `results.csv`.

Text only, no audio: `python run.py --text-mode dataset/practice/questions.csv --output outputs/text/`

Local demo UI: `python app.py`

## Environment

| Variable | Value |
| --- | --- |
| `GNANI_API_KEY` | Gnani key (speech) |
| `LLM_BASE_URL` | OpenAI-compatible endpoint, e.g. `https://openrouter.ai/api/v1` |
| `LLM_API_KEY` | LLM key |
| `LLM_MODEL` | Model with tool calling, e.g. `openai/gpt-6-luna` |
| `LLM_API_MODE` | `chat` for OpenRouter, otherwise `auto` |
| `DATASET_DIR` | `./dataset` |
| `STT_LANG` / `TTS_LANG` | `en-IN` |
| `TTS_VOICE` | `Kaveri` |
| `TTS_MODEL` | `timbre-v2.5` |

## Stack

Gnani STT and TTS · LLM via OpenRouter · multilingual-e5 + BM25 hybrid search · plain Python with tool calling · Gradio UI hosted on Modal.

## Tests

```sh
pytest -q                          # unit tests
python eval/eval_questions.py      # Step 1 vs Step 2 vs Step 3
python eval/eval_conversations.py  # multi-turn conversations
```

GitHub: https://github.com/aryacooks/voiceops
