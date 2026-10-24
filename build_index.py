import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from zentro.retriever import build_index
if __name__=='__main__':
    chunks=build_index()
    print(f'Built index: {len(chunks)} chunks (KB and product catalog).')
