"""Batch grading entry point. Each failed input gets an honest error artifact."""
import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from zentro.config import ROOT
from zentro.agent import Agent
from zentro.speech import Speech, normalize_speech, usable_transcript, REPEAT
from zentro.tools_adapter import redact

AUDIO={'.wav','.mp3','.m4a','.flac','.ogg'}
def session_key(stem):
    match=re.fullmatch(r'(.+?)(?:_turn|_)(\d+)',stem,re.I)
    return (match[1],int(match[2])) if match else (stem,0)

def run(args):
    output=Path(args.output);output.mkdir(parents=True,exist_ok=True)
    if args.text_mode:
        import pandas as pd
        rows=pd.read_csv(args.text_mode,dtype=str,keep_default_na=False).to_dict('records')
        jobs=[]
        for i,row in enumerate(rows):
            name=row.get('id') or (row.get('conversation_id','text')+'_turn'+row.get('turn',str(i+1)))
            group=('conversation:'+row['conversation_id']) if row.get('conversation_id') else 'file:'+name
            jobs.append((group,int(row.get('turn') or 0),name,row.get('asr_text',row.get('customer_message','')),False))
    else:
        folder=Path(args.input)
        if not folder.is_dir(): raise ValueError('Input must be an existing audio directory')
        jobs=[]
        for path in folder.iterdir():
            if path.suffix.lower() not in AUDIO:
                continue
            group,turn=session_key(path.stem)
            grouped=bool(re.fullmatch(r'(.+?)(?:_turn|_)(\d+)',path.stem,re.I))
            jobs.append((('conversation:' if grouped else 'file:')+group,turn,path.name,str(path),True))
    jobs.sort(key=lambda j:(j[0],j[1],j[2]))
    results=[];agents={};speech=None
    for number,(group,turn,name,source,is_audio) in enumerate(jobs,1):
        start=time.perf_counter()
        stem=Path(name).stem
        # Keep distinct encodings with the same basename from overwriting outputs.
        if sum(Path(job[2]).stem==stem for job in jobs)>1: stem=Path(name).name.replace('.','_')
        stem=re.sub(r'[^\w.-]','_',stem)
        result={'file':name,'transcript':'','reply_text':'','reply_spoken_text':'','retrieved_chunks':[],
                'cited_section_ids':[],'tool_calls':[],'latency_ms':0,'mode':'audio' if is_audio else 'text','status':'ok'}
        try:
            if is_audio:
                speech=speech or Speech()
                transcript=speech.transcribe(source)
            else: transcript=source
            result['transcript']=redact(transcript)
            if usable_transcript(transcript):
                if group not in agents: agents[group]=Agent()
                answer=agents[group].respond(transcript)
            else: answer={'reply':REPEAT,'chunks':[],'tool_calls':[],'cited_section_ids':[]}
            result.update(reply_text=answer['reply'],reply_spoken_text=normalize_speech(answer['reply']),
                          retrieved_chunks=answer['chunks'],tool_calls=answer['tool_calls'],
                          cited_section_ids=answer.get('cited_section_ids',[]))
            if is_audio:
                try:
                    speech.synthesize(answer['reply'],output/f'{stem}.reply.wav')
                    result['audio_file']=f'{stem}.reply.wav'
                except Exception as exc:
                    result.update(status='tts_error',error=f'{type(exc).__name__}: Gnani TTS failed; text retained.')
        except Exception as exc:
            result.update(status='error',error=f'{type(exc).__name__}: {redact(str(exc))}',
                          retrieved_chunks=getattr(exc,'retrieved_chunks',[]),tool_calls=getattr(exc,'tool_calls',[]))
        if group in agents: result['transcript']=agents[group].adapter.sanitize(result['transcript'])
        result['latency_ms']=round((time.perf_counter()-start)*1000,1)
        (output/f'{stem}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        results.append(result)
        print(f'[{number}/{len(jobs)}] {name}: {result["status"]} ({result["latency_ms"]} ms)',flush=True)
    (output/'results.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in results))
    fields=['file','mode','status','transcript','reply_text','reply_spoken_text','cited_section_ids','latency_ms','error']
    with (output/'results.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(results)
    failures=sum(r['status']!='ok' for r in results)
    print(f'Finished: {len(results)} inputs, {len(results)-failures} complete, {failures} errors. Output: {output.resolve()}')
    return 1 if failures else 0

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--input',help='Audio directory')
    mode.add_argument('--text-mode',help='CSV with asr_text, optional conversation_id and turn; no speech calls')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try: return run(args)
    except (ValueError,OSError) as exc: parser.error(str(exc))
if __name__=='__main__': raise SystemExit(main())
