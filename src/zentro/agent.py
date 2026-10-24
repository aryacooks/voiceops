import json
import re
from . import llm
from .prompts import AGENT, GROUNDING, BASE
from .tools_adapter import ToolAdapter, TOOLS, audit_call, redact
from .retriever import Retriever

SENTENCE=r'(?<=[.!?।])\s+'
CITATION = re.compile(r'\[([A-Za-z][A-Za-z0-9_.:-]+)\]')
IDK="I'm sorry, I don't have that information. I can connect you to a human colleague who can help."
# Policy-style facts: amounts, durations, "free". Clarifying questions and greetings carry none of these.
FACT=re.compile(r"₹|\brupees?\b|\bfree\b|\b\d+\s*(?:(?:to|-|–)\s*\d+\s*)?(?:business\s+|calendar\s+|working\s+)?(?:days?|hours?|months?|weeks?|din|दिन|घंटे|%)",re.I)
ADMITS=re.compile(r"don't have|do not have|don't know|not sure|cannot|can't|couldn't|insufficient|नहीं है|pata nahi",re.I)

def ungrounded(reply,chunks):
    """Stated facts with no valid citation (questions are exempt)."""
    statements=[s for s in re.split(SENTENCE,reply) if not s.rstrip().endswith('?')]
    return not citations(reply,chunks) and any(FACT.search(s) for s in statements) and not ADMITS.search(reply)

def citations(reply,chunks):
    valid={c['section_id'] for c in chunks}
    return sorted(set(CITATION.findall(reply)) & valid)

DONE=r"(?:issued|processed|initiated|cancelled|canceled|scheduled|booked|credited|approved|arranged|refunded)"
# The assistant claiming it performed an action ("I've cancelled", "we have just refunded").
SELF_ACTION=re.compile(r"\b(?:I|we)(?:'ve|\s+have|\s+had|\s+just|\s+already|\s+now|\s+successfully)*\s+(?:[a-z]+\s+){0,3}?"+DONE+r"\b",re.I)
# A completed state of the customer's case ("your refund has been processed"); true only if read from a verified order.
CASE_STATE=re.compile(r"\byour (?:refund|return|pickup|order|compensation|cancellation)\s+(?:has|have|was|is)\s+(?:already\s+|now\s+|successfully\s+)*(?:been\s+)?"+DONE+r"\b",re.I)
CONDITIONAL=re.compile(r"\b(?:once|after|when|if|until|as soon as|jab|agar)\b",re.I)

def unsupported_action(sentence,verified=False):
    if SELF_ACTION.search(sentence): return True
    state=CASE_STATE.search(sentence)
    # Policy explanations ("once your refund has been initiated, ...") describe rules, not actions taken.
    return bool(state) and not verified and not CONDITIONAL.search(sentence[:state.start()])

def guard_reply(reply,calls,chunks,first=False,verified=False,session_tickets=()):
    created=[c['result'] for c in calls if c['name']=='create_ticket' and c['result'].get('created') is True]
    ticket_claim=re.compile(r"(?:ticket|handover|escalation).{0,25}(?:created|raised|confirmed|submitted|ready)|(?:created|raised|escalated|transferred|handed over|sent|forwarded).{0,60}(?:ticket|team|human|agent)|TKT[0-9a-f]+",re.I)
    real_ids={r['ticket_id'] for r in created}|set(session_tickets)
    reply=re.sub(r'TKT[0-9a-f]+',lambda m:m[0] if m[0] in real_ids else '[unconfirmed ticket]',reply,flags=re.I)
    sentences=re.split(SENTENCE,reply)
    safe=[]
    for sentence in sentences:
        if unsupported_action(sentence,verified): continue
        if re.search(r'(?:refund|रिफंड|order|ऑर्डर|pickup|पिकअप|compensation).{0,35}(?:kar diya|कर दिया|कर दी|प्रोसेस कर|रद्द कर)',sentence,re.I): continue
        if not created and re.search(r'(?:ticket|टिकट|handover).{0,30}(?:bana diya|बना दिया|बना दी|bhej diya|भेज दिया)',sentence,re.I): continue
        if ticket_claim.search(sentence) and not created and not any(t in sentence for t in session_tickets): continue
        safe.append(sentence)
    reply=' '.join(safe).strip()
    valid={c['section_id'] for c in chunks}
    # A sentence whose only sources are invented is dropped; the rest of the answer survives.
    kept=[]
    for sentence in re.split(SENTENCE,reply):
        cited=CITATION.findall(sentence)
        if cited and not set(cited)&valid: continue
        kept.append(CITATION.sub(lambda m:m[0] if m[1] in valid else '',sentence))
    dropped=len(kept)<len(re.split(SENTENCE,reply))
    reply=re.sub(r'\s+([.,!?])',r'\1',' '.join(kept)).strip()
    if dropped and not created and (not reply or ungrounded(reply,chunks)): reply=IDK
    if created:
        # A real handover is always confirmed with its ID, whatever else was filtered.
        ids=[r['ticket_id'] for r in created]
        if not all(tid in reply for tid in ids): reply+=' A human colleague will contact you; your ticket ID is '+', '.join(ids)+'.'
        reply=reply.strip()
    if not reply: reply="I cannot confirm that action. I can help explain the policy or request human help."
    if first and not re.search(r'\bAI\b|artificial intelligence|एआई|कृत्रिम बुद्धिमत्ता',reply,re.I):
        reply="I'm ZentroMart's AI support assistant. "+reply
    return reply

class Agent:
    def __init__(self,retriever=None,complete=None,rewrite=None):
        self.retriever=retriever or Retriever()
        self.complete=complete or llm.complete
        # Injected LLMs (tests) get no rewrite unless one is passed explicitly.
        self.rewrite=rewrite or (llm.rewrite_query if complete is None else None)
        self.reset()
    def reset(self):
        self.turns=[]
        self.summary=''
        self.issue=''
        self.language='en-IN'
        self.adapter=ToolAdapter(self.retriever)
    def respond(self,text):
        if not str(text).strip(): return {'reply':"Sorry, I didn't catch that. Could you say it again?",'chunks':[],'tool_calls':[],'state':self.adapter.public_state()}
        self.last_raw_calls=[]
        self.adapter.observe(text)
        identity_turn=bool(re.search(r'last (?:four|4)|phone|pincode|pin code|aakhri|आख|पिन|फोन',text,re.I))
        substantive=bool(re.search(r'refund|return|cancel|damage|broken|wrong|missing|delivery|deliver|pickup|collect|credit|warrant|account|payment|charged|रिफंड|वापस|टूटा|ऑर्डर',text,re.I))
        followup=bool(re.search(r'^(?:how long|when will|what about|and |so |kitne din|kab tak)',text.strip(),re.I))
        if substantive and not identity_turn and not (self.issue and followup):
            if not self.issue or len(text.split())>8: self.issue=self.adapter.sanitize(text)[:400]
        if re.search('[\u0900-\u097f]',text): self.language='hi-IN'
        context=' | '.join(f"customer: {t['user']} / agent: {t['reply']}" for t in self.turns[-2:])
        query=self.rewrite(text,context) if self.rewrite else ''
        chunks=self.retriever.search(text,rewrite=query) if query else self.retriever.search(text)
        calls=[audit_call('search_kb',{'query':self.adapter.sanitize(text),'rewritten_query':self.adapter.sanitize(query)},{'chunks':chunks})]
        context={'state':self.adapter.public_state(),'verified_order':self.adapter.order_record(),'tickets_created_this_session':sorted(self.adapter.tickets),'summary':self.summary,'issue':self.issue,'language':self.language,'evidence':chunks}
        messages=[{'role':'system','content':AGENT+'\nTrusted session context: '+json.dumps(context,ensure_ascii=False)}]
        for turn in self.turns[-12:]:
            messages.extend([{'role':'user','content':turn['user']},{'role':'assistant','content':turn['reply']}])
        messages.append({'role':'user','content':text})
        reply=''
        for _ in range(8):
            try:
                message=self.complete(messages,tools=TOOLS)
            except Exception as exc:
                exc.retrieved_chunks=chunks
                exc.tool_calls=calls
                raise
            if not message.tool_calls:
                reply=message.content or ''
                break
            messages.append(message.model_dump(exclude_none=True))
            for call in message.tool_calls:
                try:
                    args=json.loads(call.function.arguments)
                    result=self.adapter.execute(call.function.name,args)
                except (ValueError,TypeError,KeyError,OSError) as exc:
                    args={}
                    result={'error':str(exc)}
                if call.function.name=='search_kb':
                    for chunk in result.get('chunks',[]):
                        if chunk['chunk_id'] not in {c['chunk_id'] for c in chunks}: chunks.append(chunk)
                if call.function.name=='catalog_lookup':
                    for row in result.get('products',[]):
                        sid='products.csv:'+row['sku']
                        chunks.append({'chunk_id':sid,'section_id':sid,'doc':'products.csv','score':1.0,'text':json.dumps(row)})
                self.last_raw_calls.append({'name':call.function.name,'arguments':dict(args),'result':result})
                audit=audit_call(call.function.name,args,result)
                audit=json.loads(self.adapter.sanitize(json.dumps(audit,ensure_ascii=False)))
                calls.append(audit)
                messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(result,ensure_ascii=False)})
        if not reply:
            reply="I couldn't complete the checks for that request. Could you rephrase the issue?"
        if ungrounded(reply,chunks) and not any(c['result'].get('verified') or c['result'].get('created') or c['name']=='date_calc' for c in calls):
            reply=IDK
        known={c['section_id'] for c in chunks}
        for chunk in getattr(self.retriever,'chunks',[]):
            if chunk['doc'].startswith('agent_') and chunk['section_id'] not in known and f"[{chunk['section_id']}]" in reply:
                chunks.append(dict(chunk,score=0.0)); known.add(chunk['section_id'])
        reply=guard_reply(reply,calls,chunks,first=not self.turns and not self.summary,
                          verified=self.adapter.public_state()['verified'],session_tickets=self.adapter.tickets)
        reply=self.adapter.sanitize(reply)
        self.turns=[{k:self.adapter.sanitize(v) for k,v in turn.items()} for turn in self.turns]
        self.summary=self.adapter.sanitize(self.summary)
        self.issue=self.adapter.sanitize(self.issue)
        self.turns.append({'user':self.adapter.sanitize(text),'reply':self.adapter.sanitize(reply)})
        if len(self.turns)>12:
            old=self.turns.pop(0)
            self.summary=(self.summary+' '+old['user']+' '+old['reply'])[-2400:]
        calls=json.loads(self.adapter.sanitize(json.dumps(calls,ensure_ascii=False)))
        state=self.adapter.public_state()|{'issue':self.issue,'language':self.language}
        return {'reply':reply,'chunks':chunks,'cited_section_ids':citations(reply,chunks),'tool_calls':calls,'state':state}
