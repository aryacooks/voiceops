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

def test_ticket_timeout_is_not_retried(monkeypatch):
    adapter=ToolAdapter(Search());calls=[]
    def slow(**k): calls.append(k); raise TimeoutError('ticket service timed out')
    monkeypatch.setattr(adapter.module,'create_ticket',slow)
    for _ in range(3):
        result=adapter.execute('create_ticket',{'summary':'Customer asked for a human agent about a late order'})
        assert result['created'] is False and result['uncertain']
    assert len(calls)==1 and not adapter.tickets

def test_present_tense_refund_rule_is_not_an_action_claim():
    reply=guard_reply('As a Plus member, your refund is initiated at pickup, but a card refund takes 5–7 business days [REF-2].',[],[{'section_id':'REF-2'}])
    assert 'initiated at pickup' in reply
    assert 'has been initiated' not in guard_reply('Your refund has been initiated [REF-2].',[],[{'section_id':'REF-2'}])

def test_offer_to_hand_over_survives_without_a_ticket():
    reply=guard_reply("I don't have information about refunds sent to a closed bank account, but I can connect you with a human colleague to check. Would you like me to?",[],[])
    assert 'connect you with a human colleague' in reply
    assert 'escalated' not in guard_reply('I have escalated this to a human agent.',[],[])

from zentro.rules import refund_calc,express_eta,refund_status,escalation_triggers

def test_refund_calc_coupon_clawback_and_pickup_fee():
    items=[{'price':1000,'qty':1,'category':'fashion'},{'price':600,'qty':1,'category':'fashion','return_qty':1}]
    assert refund_calc(items,160,1500,'change_of_mind')['refund_inr']==391
    assert refund_calc(items,160,1500,'change_of_mind',is_plus=True)['refund_inr']==440
    assert refund_calc(items,160,1500,'damaged',delivery_fee=40)['refund_inr']==480
    assert refund_calc([{'price':629,'qty':1,'category':'grocery','return_qty':1}],reason='change_of_mind')['eligible'] is False

def test_express_eta_cutoff_and_holiday():
    assert express_eta('2026-10-17T15:00')['expected']=='2026-10-21'
    assert express_eta('2026-10-17T13:59')['expected']=='2026-10-20'

def test_refund_status_escalates_only_past_three_days():
    assert refund_status('2026-10-12','upi')['business_days_past_max']==3
    assert refund_status('2026-10-12','upi')['escalate'] is False
    assert refund_status('2026-10-10','upi')['escalate'] is True
    assert refund_status('2026-10-17','card')['arrives_between']==['2026-10-24','2026-10-27']
    assert refund_status('2026-09-05','upi','2026-09-07','6274')['status']=='completed'

@pytest.mark.parametrize('text,rules',[
 ('connect me to a human NOW',{'ESC-1 #6'}),("I don't want to talk to a human",set()),
 ("I'm not happy, connect me to a human",{'ESC-1 #6'}),('the power bank is swelling',{'ESC-1 #7'}),
 ("it's not swelling, just warm",set()),('payment alert for a purchase I didn\'t make',{'ESC-1 #2'}),
 ("received something I didn't order",set()),('taking you to consumer court',{'ESC-1 #3'})])
def test_text_escalation_triggers(text,rules): assert {t['rule'] for t in escalation_triggers(text)}==rules

def test_data_escalation_triggers():
    tv={'sku':'ELE-0021','title':'Zentro Vista 43-inch 4K Smart TV','unit_price_inr':31649}
    monitor={'sku':'ELE-0099','title':'Orbix Studio Monitor','unit_price_inr':10000}
    assert {t['rule'] for t in escalation_triggers('status?',{'contacts_last_7_days':2})}=={'ESC-1 #4'}
    assert {t['rule'] for t in escalation_triggers('the TV screen is cracked',{'items':[tv,{'title':'Tote','unit_price_inr':979}]})}=={'ESC-1 #1'}
    assert escalation_triggers('the monitor is cracked',{'items':[monitor]})==[]
    assert escalation_triggers('when is my tote coming',{'items':[tv]})==[]
    late={'return_refund_initiated_on':'2026-07-20','return_refund_method':'upi'}
    assert {t['rule'] for t in escalation_triggers('where is my refund',late)}=={'ESC-1 #5'}

def test_agent_files_ticket_when_trigger_holds_and_model_does_not():
    agent=Agent(retriever=Search(),complete=lambda *a,**k:ChatCompletionMessage(role='assistant',content='Please stop using it immediately [DWM-5].'),rewrite=None)
    agent.adapter.module.create_ticket=lambda **k:{'created':True,'ticket_id':'TKT'+'ab'*16}
    answer=agent.respond('my power bank is swelling and hot')
    assert 'TKT'+'ab'*16 in answer['reply'] and any(c['name']=='create_ticket' for c in answer['tool_calls'])
    calm=Agent(retriever=Search(),complete=lambda *a,**k:ChatCompletionMessage(role='assistant',content='Returns are free [RET-6].'),rewrite=None)
    assert not any(c['name']=='create_ticket' for c in calm.respond("I don't need a human, just tell me about returns")['tool_calls'])

def test_record_triggers_wait_for_the_customers_issue():
    agent=Agent(retriever=Search(),complete=lambda *a,**k:None,rewrite=None)
    agent.adapter.verified_orders['48196636']={'contacts_last_7_days':2}; agent.adapter.current_order='48196636'
    assert agent.triggers('the last four digits are 4521',identity_turn=True)==[]
    assert {t['rule'] for t in agent.triggers("this is the third time I'm calling",identity_turn=False)}=={'ESC-1 #4'}
    assert agent.triggers('I lost my phone',identity_turn=True)==[]

def test_calculator_numbers_come_from_the_kb(tmp_path,monkeypatch):
    import importlib,shutil
    import zentro.config,zentro.rules
    shutil.copytree(DATASET_DIR/'kb',tmp_path/'kb')
    fee=tmp_path/'kb'/'pol_returns_v4.md'; fee.write_text(fee.read_text().replace('reverse pickup fee of ₹49','reverse pickup fee of ₹59'))
    monkeypatch.setattr(zentro.config,'DATASET_DIR',tmp_path)
    try: assert importlib.reload(zentro.rules).PICKUP_FEE==59
    finally:
        monkeypatch.undo(); importlib.reload(zentro.rules)
    assert zentro.rules.PICKUP_FEE==49 and zentro.rules.WINDOWS['card']==(5,7) and zentro.rules.HIGH_VALUE==10000

def test_customer_stated_figures_can_be_repeated_back():
    from zentro.agent import ungrounded
    assert not ungrounded('You said the product was worth ₹13,000.',[],said='the product worth 13000 is damaged')
    assert ungrounded('The product was worth ₹15,000.',[],said='the product worth 13000 is damaged')
