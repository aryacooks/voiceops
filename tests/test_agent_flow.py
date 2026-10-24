"""Scripted LLM messages exercise native tool control, without pretending to call services."""
import json
from openai.types.chat import ChatCompletionMessage
from zentro.agent import Agent
from zentro.tools_adapter import caller_numbers
from zentro.retriever import normalize_query
from test_core import Search

def message(text=None,name=None,args=None):
    return ChatCompletionMessage(role='assistant',content=text,tool_calls=[{'id':'call1','type':'function','function':{'name':name,'arguments':json.dumps(args)}}] if name else None)

def test_tool_failure_is_returned_without_false_handover(monkeypatch):
    sequence=iter([message(name='create_ticket',args={'summary':'Issue checked and requires human support'}),message('I have sent your complaint to the team.')])
    agent=Agent(retriever=Search(),complete=lambda *a,**k:next(sequence))
    def fail(**kwargs): raise OSError('disk unavailable')
    monkeypatch.setattr(agent.adapter.module,'create_ticket',fail)
    result=agent.respond('Please connect me to a person')
    assert result['tool_calls'][-1]['result']['error']=='disk unavailable'
    assert 'sent your complaint' not in result['reply']

def test_order_payload_never_in_audit_and_proof_is_redacted(monkeypatch):
    seq=iter([message(name='lookup_order',args={'order_id':'12345678','phone_last4':'0783'}),message('Your order is shipped; verification 0783.')])
    agent=Agent(retriever=Search(),complete=lambda *a,**k:next(seq))
    monkeypatch.setattr(agent.adapter.module,'lookup_order',lambda *a,**k:{'verified':True,'found':True,'status':'shipped','items':[{'secret':'private'}]})
    result=agent.respond('Order 12345678, last four 0783')
    public=json.dumps(result)
    assert '0783' not in public and 'private' not in public
    assert result['state']['verified']

def test_dates_are_not_accepted_as_caller_verification():
    agent=Agent(retriever=Search(),complete=lambda *a,**k:message('When did that happen?'))
    agent.adapter.observe('Order 12345678 refund started 17 October 2026')
    result=agent.adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'2026'})
    assert result.get('error')

def test_last_month_is_not_verification_context():
    agent=Agent(retriever=Search(),complete=lambda *a,**k:message('When did that happen?'))
    agent.adapter.observe('Order 12345678 refund started last October 2026')
    result=agent.adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'2026'})
    assert result.get('error')
    assert agent.adapter.sanitize('27 October 2026')=='27 October 2026'

def test_multiple_order_ids_preserve_caller_order():
    agent=Agent(retriever=Search(),complete=lambda *a,**k:message('Which order is this about?'))
    agent.adapter.observe('Not order 12345678; the issue is order 87654321')
    assert agent.adapter.current_order=='87654321'

def test_spoken_ids_generic():
    assert 'ELE-0012' in normalize_query('sku ele-zero zero one to pe assured')
    assert '0783' in caller_numbers('last four 0783')
    assert '12345678' in caller_numbers('order one two three four five six seven eight')

def test_issue_survives_identity_and_followup_turns():
    agent=Agent(retriever=Search(),complete=lambda *a,**k:message('Which order is this about?'))
    agent.respond('My refund has not arrived after several weeks')
    issue=agent.issue
    agent.respond('The last four digits are 6073.')
    agent.respond('How long will that take to arrive?')
    assert agent.issue==issue
    assert '6073' not in json.dumps(agent.turns)


def test_spoken_year_normalized():
    assert '2026' in normalize_query('refund started on 17 october two zero two six')
    assert '2026' in normalize_query('12 october to zero to six ko shuru hua')
