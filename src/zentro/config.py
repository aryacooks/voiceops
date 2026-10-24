from pathlib import Path
import os
from datetime import date
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')
DATASET_DIR = Path(os.getenv('DATASET_DIR', str(ROOT / 'dataset'))).resolve()
INDEX_DIR = Path(os.getenv('INDEX_DIR', str(ROOT / 'index'))).resolve()
TODAY = date(2026, 10, 20)
# Multilingual so Hindi/Hinglish questions reach English policy text (see report for the model comparison).
EMBED_MODEL = os.getenv('EMBED_MODEL', 'intfloat/multilingual-e5-base')
QUERY_PREFIX, PASSAGE_PREFIX = ('query: ', 'passage: ') if 'e5' in EMBED_MODEL else ('', '')
