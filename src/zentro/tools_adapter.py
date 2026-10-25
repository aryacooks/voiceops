import importlib.util
import re
from .config import DATASET_DIR
from .dates import date_calc
from .data import catalog_lookup, is_pincode_serviceable
from .rules import refund_calc, express_eta, refund_status, record_refund

def function(name, description, properties, required):
    return {'type':'function','function':{'name':name,'description':description,
            'parameters':{'type':'object','properties':properties,'required':required,'additionalProperties':False}}}
def string(description): return {'type':'string','description':description}
TOOLS = [
function('search_kb','Retrieve policy evidence before every policy statement.',{'query':string('Search query with context')},['query']),
function('lookup_order','Identity-gated order lookup; proof MUST have been supplied by caller.',
 {'order_id':string('8 digit order ID'),'phone_last4':string('Caller supplied 4 digits'),'pincode':string('Caller supplied delivery pincode')},['order_id']),
function('create_ticket','Create synthetic human handover. Confirm only on created=True.',
 {'summary':string('Issue, checks and reason, at least 20 characters'),'reason':string('Escalation reason')},['summary']),
function('date_calc','Deterministic arithmetic. Start excluded, today=2026-10-20. Return deadline = add_calendar_days(delivery date, window). Refund arrival = add_business_days(initiation date, min and max).',
 {'op':{'type':'string','enum':['today','add_business_days','add_calendar_days','calendar_days_between','business_days_between']},
  'start':string('ISO date YYYY-MM-DD'),'end':string('ISO date YYYY-MM-DD'),'days':{'type':'integer'}},['op']),
function('catalog_lookup','Read public product catalog facts.',{'sku':string('Exact SKU, e.g. ELE-0012')},['sku']),
function('is_pincode_serviceable','Read public pincode availability.',{'pincode':string('6 digit pincode')},['pincode']),
function('refund_calc','Exact refund for a return: coupon share and clawback (REF-4), reverse pickup fee (RET-6), delivery/COD fees (REF-5). '
 'For the verified order pass return_lines; for a hypothetical pass items. Never do this arithmetic yourself.',
 {'return_lines':{'type':'array','description':'Verified order: lines being returned','items':{'type':'object','properties':{'line_no':{'type':'integer'},'qty':{'type':'integer'}},'required':['line_no','qty']}},
  'items':{'type':'array','description':'Hypothetical order: every item, with return_qty on the returned ones','items':{'type':'object',
   'properties':{'price':{'type':'number'},'qty':{'type':'integer'},'category':string('return_category code, e.g. fashion'),'return_qty':{'type':'integer'}},'required':['price','qty']}},
  'coupon_discount':{'type':'number'},'coupon_min_order':{'type':'number'},
  'reason':{'type':'string','enum':['change_of_mind','damaged','defective','wrong_item','missing_item']},
  'is_plus':{'type':'boolean'},'delivery_fee':{'type':'number'},'cod_fee':{'type':'number'},'before_shipping':{'type':'boolean'}},[]),
function('express_eta','Express arrival date from the order time (cutoff rule in DEL-1). Omit placed_at to use the verified order.',
 {'placed_at':string('ISO date-time the order was placed, e.g. 2026-10-17T15:00')},[]),
function('refund_status','Refund arrival window (REF-2), business days past the maximum, and whether ESC-1 #5 applies. '
 'Omit arguments to use the verified order\'s refund.',
 {'initiated_on':string('ISO date the refund was initiated'),'method':{'type':'string','enum':['upi','card','netbanking','wallet','cod_wallet','cod_bank']}},[])]

def load_dataset_tools():
    spec=importlib.util.spec_from_file_location('zentro_dataset_tools',DATASET_DIR/'tools/tools.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def digit_sequences(text):
    # Normalize caller-spoken digit strings without looking at private CSVs.
    mapping={'zero':'0','oh':'0','one':'1','two':'2','three':'3','four':'4','five':'5',
             'six':'6','seven':'7','eight':'8','nine':'9'}
    lowered=text.lower()
    for word,digit in mapping.items(): lowered=re.sub(r'\b'+word+r'\b',digit,lowered)
    lowered=''.join(str(int(c)) if c.isdecimal() else c for c in lowered)
    return re.findall(r'(?<!\d)(?:\d[ -]*){4,}(?!\d)',lowered)
def caller_numbers(text):
    direct=re.findall(r'(?<!\d)(?:\d[ -]*){4,}(?!\d)',text)
    return {re.sub(r'\D','',x) for x in digit_sequences(text)+direct}

class ToolAdapter:
    def __init__(self,retriever):
        self.retriever=retriever
        self.module=load_dataset_tools()
        self.failures={}
        self.verified_orders={}
        self.caller_values=set()
        self.proof_values=set()
        self.current_order=None
        self.secrets=set()
        self.observation=0
        self.attempt_cache={}
        self.tickets=set()
        self.ticket_uncertain=None
    def observe(self,text):
        self.observation+=1
        values=caller_numbers(text)
        self.caller_values.update(values)
        proof_context=re.search(
            r'\bphone|pin\s*code|pincode|suffix|(?:last|aakhri|आख़िरी|आखिरी).{0,25}(?:four|4|चार|digits?|अंक)'
            r'|(?:four|4|चार).{0,12}(?:digits?|अंक)|पिन|फोन|फ़ोन',text,re.I)
        compact=re.sub(r'[\d\s.,-]','',text).lower()
        standalone=compact in ('','haan','yes','its',"it's",'hai') or all(word in {'zero','oh','one','two','three','four','five','six','seven','eight','nine'} for word in text.lower().split())
        # A full phone number (optionally +91) is unambiguous in any wording ("my number is ...") and proves its last 4.
        full=[v for v in values if len(v)==10 or (len(v)==12 and v.startswith('91'))]
        self.proof_values.update(v[-4:] for v in full)
        self.secrets.update(full)
        # A short reply while an order awaits verification is the answer ("0110, sorry I mean 0101").
        awaiting=self.current_order and self.current_order not in self.verified_orders and len(text.split())<=8
        if proof_context or standalone or awaiting:
            submitted={v for v in values if len(v) in (4,6)}
            self.proof_values.update(submitted)
            self.secrets.update(submitted)
        # Caller order, rather than set iteration, determines the active order.
        orders=[re.sub(r'\D','',v) for v in digit_sequences(text) if len(re.sub(r'\D','',v))==8]
        if orders: self.current_order=orders[-1]
    def execute(self,name,args):
        if name=='search_kb': return {'chunks':self.retriever.search(args['query'])}
        if name=='date_calc': return date_calc(**args)
        if name=='catalog_lookup': return {'products':catalog_lookup(args['sku'])}
        if name=='is_pincode_serviceable': return is_pincode_serviceable(args['pincode'])
        record=self.verified_orders.get(self.current_order)
        if name=='refund_calc':
            if args.get('return_lines'):
                if not record: return {'error':'Verify the order first, or pass items for a hypothetical.'}
                chosen={int(l['line_no']):int(l['qty']) for l in args['return_lines']}
                items=[{'price':i['unit_price_inr'],'qty':i['qty'],'category':i['return_category'],'return_qty':min(chosen.get(int(i['line_no']),0),i['qty'])} for i in record['items']]
                return refund_calc(items,record.get('coupon_discount_inr') or 0,record.get('coupon_min_order_inr') or 0,args.get('reason'),
                                   bool(record.get('is_plus')),record.get('delivery_fee_inr') or 0,record.get('cod_fee_inr') or 0,bool(args.get('before_shipping')))
            if not args.get('items'): return {'error':'Pass return_lines (verified order) or items (hypothetical).'}
            return refund_calc(args['items'],args.get('coupon_discount') or 0,args.get('coupon_min_order') or 0,args.get('reason'),
                               bool(args.get('is_plus')),args.get('delivery_fee') or 0,args.get('cod_fee') or 0,bool(args.get('before_shipping')))
        if name=='express_eta':
            placed=args.get('placed_at') or (record or {}).get('placed_at')
            return express_eta(placed) if placed else {'error':'Ask when the order was placed (date and time).'}
        if name=='refund_status':
            if args.get('initiated_on') and args.get('method'): return refund_status(args['initiated_on'],args['method'])
            refund=record_refund(record) if record else None
            if not refund: return {'error':'No refund on a verified order; ask for the order ID or the initiation date and method.'}
            return {'refund':refund['kind']}|refund_status(refund['initiated_on'],refund['method'],refund['completed_on'],refund['rrn'])
        if name=='lookup_order':
            oid=re.sub(r'\D','',str(args['order_id']))
            if len(oid)!=8: return {'error':'Order IDs are 8 digits; ask the caller to re-check it.'}
            if oid not in self.caller_values: return {'error':'Ask caller for the order ID; do not infer it.'}
            if oid in self.verified_orders: return self.verified_orders[oid]
            cache_key=(oid,self.observation,args.get('phone_last4') or args.get('pincode'))
            if cache_key in self.attempt_cache: return self.attempt_cache[cache_key]
            if self.failures.get(oid,0)>=2: return {'verified':False,'locked':True,'message':'Two failed checks. Offer general policy or registered-phone support.'}
            proof=args.get('phone_last4') or args.get('pincode')
            if proof:
                proof=re.sub(r'\D','',str(proof))
                if len(proof)==10 or (len(proof)==12 and proof.startswith('91')): proof=proof[-4:]
                if proof not in self.proof_values or len(proof) not in (4,6):
                    return {'error':'Verification value must be supplied by this caller, not guessed.'}
            if proof: self.secrets.add(proof)
            result=self.module.lookup_order(oid,verification_value=proof)
            if result.get('verified'):
                self.verified_orders[oid]=result
                self.current_order=oid
            elif proof: self.failures[oid]=self.failures.get(oid,0)+1
            self.attempt_cache[cache_key]=result
            return result
        if name=='create_ticket':
            # After a timeout the write may have landed; retrying could file duplicates, so later calls get the same answer.
            if self.ticket_uncertain: return self.ticket_uncertain
            try:
                result=self.module.create_ticket(summary=self.sanitize(args['summary']),order_id=self.current_order,reason=self.sanitize(args.get('reason') or ''))
            except (TimeoutError,ConnectionError) as exc:
                self.ticket_uncertain={'created':False,'uncertain':True,'error':f'{exc}. The ticket may or may not have been saved; do not retry.'}
                return self.ticket_uncertain
            if result.get('created'): self.tickets.add(result['ticket_id'])
            return result
        raise ValueError('Unknown tool')
    def sanitize(self,text):
        return redact(text,self.secrets)
    def order_record(self):
        """The verified order, minus contact details (IDV-4), so later turns can answer from it."""
        record=self.verified_orders.get(self.current_order)
        if not record: return None
        return {k:v for k,v in record.items() if not re.search(r'phone|email|address|street|customer_id|pincode',k)}
    def public_state(self):
        oid=self.current_order
        return {'order_id':oid,'verified':oid in self.verified_orders,'verification_failures':self.failures.get(oid,0)}

def redact(text,secrets=()):
    text=str(text)
    for secret in sorted(secrets,key=len,reverse=True):
        # Preserve ordinary years/amounts; redact only caller proof values in session.
        text=re.sub(r'(?<![0-9A-Za-z])'+r'[ -]*'.join(re.escape(c) for c in secret)+r'(?![0-9A-Za-z])','[verification redacted]',text)
    text=re.sub(r'[\w.+-]+@[\w.-]+\.[a-zA-Z]+','[email redacted]',text)
    # Alphanumeric boundaries keep digit runs inside ticket IDs (TKT…) intact.
    text=re.sub(r'(?<![0-9A-Za-z])(?:\+91[ -]?)?(?:\d{10}|\d{5}[ -]\d{5}|\d{3}[ -]\d{3}[ -]\d{4})(?![0-9A-Za-z])','[phone redacted]',text)
    return text

def audit_call(name,args,result):
    public_args={k:('[redacted]' if k in ('phone_last4','pincode') and name=='lookup_order' else redact(v) if isinstance(v,str) else v) for k,v in args.items()}
    if name=='lookup_order': public_result={k:v for k,v in result.items() if k in ('found','verified','verification_required','locked','error','message')}
    elif name=='search_kb': public_result={'section_ids':[c['section_id'] for c in result.get('chunks',[])]}
    else: public_result=result
    return {'name':name,'arguments':public_args,'result':public_result}
