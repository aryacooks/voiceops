"""Batch orchestration checks; scripted text responses never call an external service."""
import csv
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


def load_runner():
    path=Path(__file__).resolve().parents[1]/'run.py'
    spec=importlib.util.spec_from_file_location('voiceops_test_runner',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_batch_numeric_order_session_isolation_and_failure_recovery(tmp_path,monkeypatch):
    runner=load_runner()
    sessions=[]
    class ScriptedAgent:
        def __init__(self):
            self.seen=[]
            self.adapter=SimpleNamespace(sanitize=lambda text:text)
            sessions.append(self.seen)
        def respond(self,text):
            self.seen.append(text)
            if text=='failing turn':
                raise RuntimeError('scripted failure')
            return {'reply':'Scripted test response.','chunks':[],'tool_calls':[]}
    monkeypatch.setattr(runner,'Agent',ScriptedAgent)
    source=tmp_path/'input.csv'
    with source.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['id','conversation_id','turn','asr_text'])
        writer.writeheader()
        writer.writerows([
            {'id':'turn10','conversation_id':'conv','turn':'10','asr_text':'final turn'},
            {'id':'turn2','conversation_id':'conv','turn':'2','asr_text':'failing turn'},
            {'id':'turn1','conversation_id':'conv','turn':'1','asr_text':'first turn'},
            {'id':'conv','asr_text':'independent question'},
        ])
    output=tmp_path/'out'
    assert runner.run(SimpleNamespace(text_mode=source,input=None,output=output))==1
    assert ['first turn','failing turn','final turn'] in sessions
    assert ['independent question'] in sessions
    records=[json.loads(line) for line in (output/'results.jsonl').read_text().splitlines()]
    assert len(records)==4
    assert sum(record['status']=='error' for record in records)==1
    assert (output/'turn10.json').is_file()
    assert not list(output.glob('*.wav'))


def test_audio_turn_filename_parser():
    runner=load_runner()
    assert runner.session_key('case_turn10')==('case',10)
    assert runner.session_key('case_2')==('case',2)
    assert runner.session_key('independent')==('independent',0)
