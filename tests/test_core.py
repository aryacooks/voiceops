from datetime import date
import json
from types import SimpleNamespace
import pytest
from openai.types.chat import ChatCompletionMessage
from zentro.dates import add_business_days,date_calc
from zentro.kb import load_chunks
from zentro.tools_adapter import ToolAdapter,redact
from zentro.agent import Agent,guard_reply
from zentro.speech import normalize_speech,usable_transcript
from zentro.config import DATASET_DIR
from judge import expected_tools,evidence_recall

@pytest.mark.parametrize('start,days,expected',[
 ('2026-10-01',1,'2026-10-03'),('2026-10-17',1,'2026-10-20'),
 ('2026-10-17',7,'2026-10-27'),('2026-11-07',1,'2026-11-10'),
 ('2026-10-20',-1,'2026-10-17'),('2026-10-20',0,'2026-10-20')])
def test_business_days(start,days,expected): assert add_business_days(start,days).isoformat()==expected

def test_calendar_days():
    assert date_calc('add_calendar_days','2026-10-17',days=7)['date']=='2026-10-24'
    assert date_calc('business_days_between','2026-10-17',end='2026-10-20')['days']==1

def test_chunks_and_catalog():
    chunks=load_chunks(); ids={c['section_id'] for c in chunks}
    assert {'RET-2','RETv3-2','products.csv:ELE-0012'}<=ids
    assert all('support_logs' not in c['doc'] for c in chunks)
    assert len({c['chunk_id'] for c in chunks})==len(chunks)

class Search:
    def search(self,query,k=5): return [{'chunk_id':'x','section_id':'REF-2','doc':'policy.md','text':'Refund rules','score':1}]

def test_verification_is_caller_gated_and_retry_limited(monkeypatch):
    adapter=ToolAdapter(Search());adapter.observe('My order 12345678')
    calls=[]
    def lookup(order_id,verification_value=None):
        calls.append(verification_value)
        return {'verified':False,'verification_required':True}
    monkeypatch.setattr(adapter.module,'lookup_order',lookup)
    assert adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'9999'}).get('error')
    assert not calls
    adapter.observe('1234')
    adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'1234'})
    adapter.observe('4321')
    adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'4321'})
    adapter.observe('try 4321 again')
    assert adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'4321'})['locked']
    assert len(calls)==2
    assert adapter.sanitize('Refund due 2026; suffix 1234')=='Refund due 2026; suffix [verification redacted]'

def test_real_tool_never_exposes_unverified_order():
    adapter=ToolAdapter(Search())
    adapter.observe('Order 12345678')
    result=adapter.execute('lookup_order',{'order_id':'12345678'})
    assert result['verification_required'] and 'items' not in result and 'status' not in result

def test_ticket_error_does_not_confirm_handover(monkeypatch):
    agent=Agent(retriever=Search(),complete=lambda *a,**k:ChatCompletionMessage(role='assistant',content='Your ticket is ready.'))
    answer=agent.respond('Help me please')
    assert 'Your ticket is ready' not in answer['reply']
    assert 'AI' in answer['reply']

def test_spoken_normalization():
    spoken=normalize_speech('Refund ₹500 on 2026-10-25 for order 12345678. [REF-2]')
    assert spoken=='Refund 500 rupees on 25 October 2026 for order 1 2 3 4, 5 6 7 8.'
    assert '2026' in normalize_speech('By 25 October.')
    assert not usable_transcript('[noise]') and not usable_transcript('')

def test_expected_tools_leading_zero():
    assert expected_tools('lookup_order(order_id=12345678, verification_value=0783)')[0][1]['verification_value']=='0783'
    assert evidence_recall('RET-2 ; products.csv:ELE-0012',[{'section_id':'RET-2'}])==0.5

def test_year_is_not_a_secret_until_used_as_proof(monkeypatch):
    adapter=ToolAdapter(Search());adapter.observe('My refund started 17 October 2026, order 12345678')
    assert adapter.sanitize('Due 27 October 2026')=='Due 27 October 2026'
    adapter.observe('last four 0783')
    monkeypatch.setattr(adapter.module,'lookup_order',lambda *a,**k:{'verified':False})
    args={'order_id':'12345678','phone_last4':'0783'}
    adapter.execute('lookup_order',args);adapter.execute('lookup_order',args)
    assert adapter.failures['12345678']==1
    assert adapter.sanitize('Proof 0783; due 2026')=='Proof [verification redacted]; due 2026'
    adapter.observe('0783');adapter.execute('lookup_order',args)
    assert adapter.failures['12345678']==2

def test_invalid_citation_replaces_unsupported_claim():
    assert '500 rupees' not in guard_reply('Everyone gets 500 rupees. [FAKE-9]',[],[{'section_id':'REF-2'}])


def test_verified_order_is_remembered_without_contact_details():
    adapter=ToolAdapter(Search());adapter.observe('Order 89782837, last four digits 4533')
    result=adapter.execute('lookup_order',{'order_id':'89782837','phone_last4':'4533'})
    assert result.get('verified')
    record=adapter.order_record()
    assert record['order_id']=='89782837' and 'status' in record
    assert not any(k for k in record if 'phone' in k or 'pincode' in k or 'address' in k)


def test_ticket_from_earlier_turn_stays_confirmed():
    tid='TKT'+'4533'+'e'*28
    reply=guard_reply(f'Your ticket ID is {tid}.',[],[],session_tickets={tid})
    assert tid in reply and 'unconfirmed' not in reply


def test_headphones_year_is_not_treated_as_proof():
    adapter=ToolAdapter(None)
    adapter.observe('my headphones were delivered on 25 july 2026')
    assert adapter.sanitize('delivered on 25 July 2026')=='delivered on 25 July 2026'


def test_ticket_id_digits_are_not_redacted_as_phone():
    ticket='TKT'+'4500012345'+'a'*22
    assert redact('your ticket ID is '+ticket)=='your ticket ID is '+ticket
    assert redact('call 9876543210')=='call [phone redacted]'

def test_malformed_order_id_is_rejected_without_a_lookup(monkeypatch):
    adapter=ToolAdapter(Search());adapter.observe('my order 1001 is late')
    monkeypatch.setattr(adapter.module,'lookup_order',lambda *a,**k:pytest.fail('lookup ran'))
    assert '8 digits' in adapter.execute('lookup_order',{'order_id':'1001'})['error']
    assert adapter.public_state()['verification_failures']==0

def test_full_phone_number_verifies_by_its_last_four(monkeypatch):
    adapter=ToolAdapter(Search());adapter.observe('My order 12345678')
    seen=[]
    monkeypatch.setattr(adapter.module,'lookup_order',lambda order_id,verification_value=None:seen.append(verification_value) or {'verified':True})
    adapter.observe('my phone number is +91 98765 43210')
    assert adapter.execute('lookup_order',{'order_id':'12345678','phone_last4':'+919876543210'})['verified']
    assert seen==['3210']
    assert '98765' not in adapter.sanitize('you said 9876543210 and +91 98765 43210')

def test_spaced_phone_numbers_are_redacted_anywhere():
    for number in ('98765 43210','+91 98765 43210','987-654-3210','+91-9876543210'):
        assert redact('reach me on '+number)=='reach me on [phone redacted]'

def test_full_phone_counts_as_proof_without_the_word_phone():
    adapter=ToolAdapter(Search());adapter.observe('my number is +91 98765 43210')
    assert '3210' in adapter.proof_values

def test_short_reply_while_awaiting_verification_is_proof():
    adapter=ToolAdapter(Search());adapter.observe('my order 12345678 is late')
    adapter.observe('0110 sorry I mean 0101')
    assert {'0110','0101'}<=adapter.proof_values
    adapter.observe('the refund was due in 2026 but it never came and nobody called me back')
    assert '2026' not in adapter.proof_values
