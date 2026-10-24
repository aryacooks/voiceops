import argparse
import json
import os
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pandas as pd
from zentro.config import DATASET_DIR
from zentro.agent import Agent
from judge import judge,judge_context,tool_match,evidence_recall

def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    frame=pd.read_csv(DATASET_DIR/'practice/conversations.csv',dtype=str,keep_default_na=False)
    frame['turn_number']=frame.turn.astype(int)
    enabled=bool(os.getenv('LLM_API_KEY') and os.getenv('LLM_MODEL'))
    results=[]
    for cid,group in frame.groupby('conversation_id',sort=True):
        agent=Agent() if enabled else None
        for row in group.sort_values('turn_number').to_dict('records'):
            result={'conversation_id':cid,'turn':row['turn'],'expected_decision':row['expected_decision'],
                    'expected_tool_calls':re.sub(r'(verification_value|phone_last4|pincode)=([^,)]+)',r'\1=[redacted]',row['expected_tool_calls']),'reply':'','decision_correct':None,
                    'tool_recall':None,'evidence_recall':None,'status':'not_run_no_credentials'}
            if enabled:
                try:
                    answer=agent.respond(row['customer_message'])
                    score=judge(row,answer['reply'],judge_context(answer['chunks'],answer['reply'],agent.last_raw_calls,list(agent.adapter.verified_orders.values())))
                    result.update(reply=answer['reply'],decision=score['decision'],decision_correct=int(score['decision']==row['expected_decision']),
                                  correctness=score['correct'],judge_reason=score['reason'],tool_calls=answer['tool_calls'],
                                  tool_recall=tool_match(row['expected_tool_calls'],agent.last_raw_calls),
                                  evidence_recall=evidence_recall(row['gold_evidence'],answer['chunks']),status='ok')
                except Exception as exc: result.update(status='error',error=type(exc).__name__+': '+str(exc))
            results.append(result)
    pd.DataFrame(results).to_csv(out/'conversations.csv',index=False)
    (out/'conversations.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    metrics={'conversations':frame.conversation_id.nunique(),'turns':len(frame),'scored_turns':sum(r['status']=='ok' for r in results)}
    for key in ('correctness','decision_correct','tool_recall','evidence_recall'):
        values=[r[key] for r in results if r.get(key) is not None]
        metrics[key]=sum(values)/len(values) if values else None
    (out/'conversation_summary.json').write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='eval/results');run(parser.parse_args())
