"""Run retrieval-only offline or full Step 1/2 + independent LLM judging."""
import argparse
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
from zentro.config import DATASET_DIR
from zentro.retriever import Retriever
from zentro.agent_step1 import answer as baseline
from zentro.agent_step2 import answer as rag
from judge import evidence_recall,judge,judge_context
from zentro.agent import Agent

STAGES=('step1','step2','step3')
def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    data=pd.read_csv(DATASET_DIR/'practice/questions.csv',dtype=str,keep_default_na=False)
    retriever=Retriever();results=[]
    enabled=not args.retrieval_only and bool(os.getenv('LLM_API_KEY') and os.getenv('LLM_MODEL'))
    for row in data.to_dict('records'):
        chunks=retriever.search(row['asr_text'])
        for stage in STAGES:
            result={'id':row['id'],'stage':stage,'question':row['asr_text'],'gold_evidence':row['gold_evidence'],
                    'retrieved_section_ids':[c['section_id'] for c in chunks] if stage!='step1' else [],
                    'evidence_recall_at_5':evidence_recall(row['gold_evidence'],chunks if stage!='step1' else []),
                    'reply':'','correctness':None,'idk_correct':None,'status':'not_run_no_credentials' if not enabled else 'pending'}
            if args.retrieval_only: result['status']='retrieval_only'
            if enabled:
                try:
                    if stage=='step3':
                        # The full agent, exactly as run.py uses it, on a fresh session per question.
                        agent=Agent(retriever=retriever);response=agent.respond(row['asr_text'])
                        context=judge_context(response['chunks'],response['reply'],agent.last_raw_calls,list(agent.adapter.verified_orders.values()))
                    else:
                        response=baseline(row['asr_text']) if stage=='step1' else rag(row['asr_text'],retriever)
                        context=judge_context(response.get('chunks',[]),response['reply'])
                    score=judge(row,response['reply'],context)
                    if stage!='step1':
                        # Score retrieval on what the RAG answer actually used (raw ASR + LLM rewrite).
                        result.update(retrieved_section_ids=[c['section_id'] for c in response['chunks']],rewritten_query=response.get('rewritten_query',''),
                                      evidence_recall_raw_asr=result['evidence_recall_at_5'],evidence_recall_at_5=evidence_recall(row['gold_evidence'],response['chunks']))
                    result.update(reply=response['reply'],correctness=score['correct'],decision=score['decision'],judge_reason=score['reason'],
                                  idk_correct=int(score['idk']) if row['answerable']=='False' else None,status='ok')
                except Exception as exc: result.update(status='error',error=type(exc).__name__+': '+str(exc))
            results.append(result)
        print(row['id'],[c['section_id'] for c in chunks],flush=True)
    frame=pd.DataFrame(results);frame.to_csv(out/'questions.csv',index=False)
    (out/'questions.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    lines=['# Evaluation summary','',f'Questions: {len(data)}. Retrieval: multilingual-e5-base + BM25 RRF (+ LLM query rewrite when enabled), top five. Full LLM evaluation enabled: {enabled}.','',
           '| Stage | LLM items scored | Correctness | Evidence recall@5 (macro) | Unanswerable IDK accuracy |',
           '| --- | ---: | ---: | ---: | ---: |']
    for stage in STAGES:
        subset=frame[frame.stage==stage]
        scored=subset.correctness.dropna();idk=subset.idk_correct.dropna()
        fmt=lambda values:f'{values.mean():.3f}' if len(values) else 'Not run'
        lines.append(f'| {stage} | {len(scored)} | {fmt(scored)} | {fmt(subset.evidence_recall_at_5.dropna())} | {fmt(idk)} |')
    lines+=['','Recall is the fraction of gold section/catalog IDs in the retrieved five, macro-averaged over rows with gold evidence. Baseline has no retrieved evidence by design. Retrieval numbers are not answer correctness. No answer/judge calls run when credentials are absent.','',
            'Conversation evaluation is a separate command. Its missing scores must not be inferred from retrieval results.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    return results
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retrieval-only',action='store_true')
    parser.add_argument('--output',default='eval/results')
    run(parser.parse_args())
