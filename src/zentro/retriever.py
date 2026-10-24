import hashlib
import json
import os
import re
from functools import lru_cache
import numpy as np
from rank_bm25 import BM25Okapi
from .config import DATASET_DIR, INDEX_DIR, EMBED_MODEL, QUERY_PREFIX, PASSAGE_PREFIX
from .kb import load_chunks

DIGITS={'zero':'0','oh':'0','one':'1','two':'2','to':'2','three':'3','four':'4','five':'5','six':'6','seven':'7','eight':'8','nine':'9'}
SKU_PREFIXES='ELE|FSH|HOM|BKS|INR|BTY|BEA|GRC|DGT'

def normalize_query(text):
    """Rejoin SKUs that ASR spells out digit by digit ("ele-zero zero one to" -> ELE-0012)."""
    def sku(match):
        tail=re.findall(r'[a-z]+|\d',match[2].lower())
        return match[1].upper()+'-'+''.join(DIGITS.get(word,word) for word in tail)+' '
    word='zero|oh|one|two|to|three|four|five|six|seven|eight|nine|\\d'
    text=re.sub(rf'\b({SKU_PREFIXES})[ -]+((?:(?:{word})[ -]*){{4}})',sku,text,flags=re.I)
    # Spoken years ("two zero two six", "to zero to six") -> 2026.
    year=lambda m:''.join(DIGITS.get(w,w) for w in m[0].lower().split())
    return re.sub(r'\b(?:two|to)\s+(?:zero|oh)\s+(?:two|to)\s+(?:zero|one|two|three|four|five|six|seven|eight|nine)\b',year,text,flags=re.I)

def tokens(text): return re.findall(r'[\w]+',text.lower())
def fingerprint():
    paths=sorted((DATASET_DIR/'kb').glob('*.md'))+[DATASET_DIR/'data/products.csv']
    return hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()
@lru_cache(maxsize=1)
def encoder():
    os.environ.setdefault('HF_HUB_DISABLE_IMPLICIT_TOKEN','1')
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL,token=False)
def build_index():
    chunks=load_chunks()
    vectors=encoder().encode([PASSAGE_PREFIX+c['text'] for c in chunks],normalize_embeddings=True,show_progress_bar=True)
    INDEX_DIR.mkdir(parents=True,exist_ok=True)
    np.save(INDEX_DIR/'embeddings.npy',vectors)
    (INDEX_DIR/'chunks.json').write_text(json.dumps(chunks,ensure_ascii=False,indent=2))
    (INDEX_DIR/'manifest.json').write_text(json.dumps({'model':EMBED_MODEL,'source_hash':fingerprint(),'chunks':len(chunks)}))
    return chunks

PRIORITY={'pol':1.10,'agent':1.07,'help':1.04,'faq':1.02,'mkt':1,'meta':1.05}
STOP={'the','a','of','for','and','in','i','my','to','with','can','it','is','get','how','on','return','sku','pack','pe','hai','kya'}

class Retriever:
    def __init__(self):
        manifest=INDEX_DIR/'manifest.json'
        try:
            info=json.loads(manifest.read_text())
            valid=info.get('source_hash')==fingerprint() and info.get('model')==EMBED_MODEL
            meta=json.loads((INDEX_DIR/'chunks.json').read_text())
            matrix=np.load(INDEX_DIR/'embeddings.npy',allow_pickle=False)
            valid=valid and matrix.ndim==2 and matrix.shape[0]==len(meta)==info.get('chunks')
        except (OSError,ValueError,KeyError): valid=False
        if not valid: build_index()
        self.chunks=json.loads((INDEX_DIR/'chunks.json').read_text())
        self.vectors=np.load(INDEX_DIR/'embeddings.npy',allow_pickle=False)
        self.documents=[i for i,c in enumerate(self.chunks) if c['doc_type']!='catalog']
        self.catalog=[i for i,c in enumerate(self.chunks) if c['doc_type']=='catalog']
        self.bm25=BM25Okapi([tokens(self.chunks[i]['text']) for i in self.documents])

    def products(self,query):
        """Catalog rows named in the query, by exact SKU or by most of the product title."""
        exact=re.findall(r'\b[A-Z]{3}-\d{4}\b',query.upper())
        found=[i for i in self.catalog if self.chunks[i]['section_id'].split(':')[1] in exact]
        if found: return found[:2]
        words=set(tokens(query))-STOP
        scored=[]
        for i in self.catalog:
            title=re.search(r'title: ([^;]+)',self.chunks[i]['text'])
            title_words=set(tokens(title[1]))-STOP if title else set()
            overlap=len(title_words&words)
            if overlap>=2 and overlap/max(1,len(title_words))>=0.6: scored.append((overlap/len(title_words),i))
        return [i for _,i in sorted(scored,reverse=True)[:1]]

    def rank(self,query,scores,weight=1.0):
        vector=encoder().encode([QUERY_PREFIX+query],normalize_embeddings=True)[0]
        similarity=self.vectors[self.documents]@vector
        lexical=self.bm25.get_scores(tokens(query))
        # Dense carries the multilingual signal; BM25 helps exact English terms but over-matches the Hindi FAQ.
        for ranking,w in ((np.argsort(-similarity),1.0),(np.argsort(-lexical),0.5)):
            for rank,pos in enumerate(ranking[:40]):
                idx=self.documents[pos]
                scores[idx]=scores.get(idx,0)+weight*w/(60+rank+1)

    def search(self,query,k=5,rewrite=None):
        query=normalize_query(query)
        scores={}
        # The LLM rewrite is clean English; the raw transcript keeps exact names/SKUs but is noisier.
        self.rank(query,scores,weight=0.5 if rewrite else 1.0)
        if rewrite and rewrite.strip().lower()!=query.strip().lower(): self.rank(normalize_query(rewrite),scores)
        products=self.products(query+' '+(rewrite or ''))
        for idx in products:
            # Route through the product's own catalog facts so category-specific policy (return window, warranty) is found.
            facts=re.sub(r'description: .*','',self.chunks[idx]['text'])
            self.rank(facts,scores,weight=0.7)
        candidates=sorted(scores,key=scores.get,reverse=True)[:12]
        current=[self.chunks[i] for i in candidates if self.chunks[i]['status']!='superseded']
        for idx in candidates:
            c=self.chunks[idx]
            scores[idx]*=PRIORITY.get(c['doc_type'],1)
            if c['status']=='superseded':
                # KB-00.1: a superseded document applies only where its successor says it still does.
                major=c.get('version','').split('.')[0]
                cited=any(s.get('doc_id')==c.get('superseded_by') and major and re.search(rf'\bversion {major}\b',s['text'],re.I) for s in current)
                scores[idx]*=0.9 if cited else 0.08
        slots=max(1,k-len(products))
        chosen=sorted(candidates,key=lambda i:scores[i],reverse=True)[:slots]+products
        for idx in products: scores[idx]=0.04
        chosen=self.with_rules(chosen[:k],candidates,k)
        return [dict(self.chunks[i],score=round(scores.get(i,0.02),6)) for i in chosen]

    def with_rules(self,chosen,candidates,k):
        """Attach the KB-00 rule a retrieved chunk depends on (calendar or document precedence), dropping the weakest chunk."""
        texts=[self.chunks[i] for i in chosen]
        rules=[]
        if any('business day' in c['text'].lower() for c in texts if c['doc_type']!='meta'): rules.append('KB-00.3')
        types={self.chunks[i]['doc_type'] for i in candidates[:8]}
        if 'pol' in types and types&{'faq','mkt'}: rules.append('KB-00.1')
        for rule in rules:
            idx=next((i for i,c in enumerate(self.chunks) if c['section_id']==rule),None)
            if idx is None or idx in chosen: continue
            weakest=next((n for n in range(len(chosen)-1,-1,-1) if self.chunks[chosen[n]]['doc_type'] not in ('catalog','meta')),None)
            if len(chosen)>=k and weakest is not None: chosen.pop(weakest)
            if len(chosen)<k: chosen.append(idx)
        return chosen
