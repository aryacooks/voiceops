"""Hosts the Gradio demo on Modal: `modal deploy modal_app.py`.

API keys come from the Modal secret `voiceops` (LLM_API_KEY, GNANI_API_KEY); non-secret settings are read from the local
.env at deploy time. The dataset and index are uploaded from this folder, so extract the dataset and build the index first.
"""
from pathlib import Path
import modal

ROOT = Path(__file__).resolve().parent
PUBLIC = ('LLM_BASE_URL', 'LLM_MODEL', 'LLM_API_MODE', 'STT_LANG', 'TTS_LANG', 'TTS_VOICE', 'TTS_MODEL', 'QUERY_REWRITE', 'EMBED_MODEL')

def settings():
    from dotenv import dotenv_values
    values = dotenv_values(ROOT / '.env') if (ROOT / '.env').exists() else {}
    return {k: values[k] for k in PUBLIC if values.get(k)}

def download_model():
    # Baked into the image so a cold start loads the model from disk instead of downloading 1.1 GB.
    import os
    from sentence_transformers import SentenceTransformer
    SentenceTransformer(os.getenv('EMBED_MODEL', 'intfloat/multilingual-e5-base'), token=False)

# Modal re-imports this file inside the container, where the local requirements and .env do not exist.
LOCAL = modal.is_local()
requirements = [line for line in (ROOT / 'requirements.txt').read_text().split() if line and not line.startswith('pytest')] if LOCAL else []
image = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install('ffmpeg')
    # CPU-only torch keeps the image small; sentence-transformers would otherwise pull the CUDA build.
    .pip_install('torch==2.14.1', index_url='https://download.pytorch.org/whl/cpu')
    .pip_install(*requirements)
    .env({'HF_HOME': '/models', 'GRADIO_ANALYTICS_ENABLED': 'False', **(settings() if LOCAL else {})})
    .run_function(download_model)
    .add_local_file(ROOT / 'app.py', '/app/app.py')
    .add_local_dir(ROOT / 'src', '/app/src', ignore=['**/__pycache__'])
    .add_local_dir(ROOT / 'dataset', '/app/dataset', ignore=['practice', 'tools/tickets_created.csv', '**/__pycache__'])
    .add_local_dir(ROOT / 'index', '/app/index')
)
app = modal.App('voiceops', image=image)

# One container: Gradio keeps each conversation in that process's memory. It sleeps after 5 idle minutes.
@app.function(secrets=[modal.Secret.from_name('voiceops')], cpu=1, memory=3072, max_containers=1,
              scaledown_window=300, timeout=900)
@modal.concurrent(max_inputs=50)
@modal.asgi_app()
def web():
    import os
    import sys
    import gradio as gr
    from fastapi import FastAPI
    os.chdir('/app')
    sys.path.insert(0, '/app')
    import app as demo
    from zentro.retriever import encoder
    demo.REPLY_DIR.mkdir(parents=True, exist_ok=True)
    encoder()
    return gr.mount_gradio_app(FastAPI(), demo.build_app(), path='/', allowed_paths=[str(demo.REPLY_DIR)])
