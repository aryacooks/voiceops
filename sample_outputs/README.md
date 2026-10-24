# Sample outputs

Produced by the grading command on 24 October 2026 with live Gnani STT/TTS and `openai/gpt-6-luna` (OpenRouter):

```sh
python run.py --input sample_outputs/inputs --output sample_outputs
```

| Input | What it tests |
|---|---|
| `demo_turn1/2/3.wav` | One session (files sharing a prefix with `_turnN` are grouped): cancel request → caller verification → ₹500 compensation demand, refused and handed over with a real ticket |
| `wallet_refund.wav` | Grounded policy answer (REF-2) |
| `hindi_return.wav` | Hindi question, answered in the caller's language |
| `unknown_question.wav` | Not covered by the KB → "I don't know" + offer of a human colleague |

The input clips were generated with Gnani TTS voices (Pranav, Shlok, Trupti), distinct from the reply voice (Kaveri), so the pipeline uses no non-Gnani speech service anywhere. They are pipeline test inputs, not recordings of a person.

Each `<name>.json` holds the transcript, reply text, spoken text, retrieved chunks, cited section IDs, tool audit and latency; `<name>.reply.wav` is the Gnani reply; `results.jsonl` / `results.csv` summarise the batch.
