"""Deterministic policy arithmetic and escalation triggers, so money, dates and handovers never depend on the model."""
import re
from datetime import datetime
from .config import DATASET_DIR, TODAY
from .dates import add_business_days, date_calc

def section(sid):
    """Body of a current KB section, e.g. section('REF-2'). Superseded documents are skipped."""
    for path in sorted((DATASET_DIR / 'kb').glob('*.md')):
        text = path.read_text()
        if 'superseded' in path.name: continue
        match = re.search(rf'^## \[{re.escape(sid)}\][^\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
        if match: return match[1]
    raise LookupError(f'KB section {sid} not found; the calculators read their numbers from it.')

def need(pattern, text, sid):
    match = re.search(pattern, text, re.I)
    if not match: raise LookupError(f'Could not read {pattern!r} from KB section {sid}.')
    return match

def table(sid):
    return [[c.strip() for c in line.strip().strip('|').split('|')] for line in section(sid).splitlines()
            if line.startswith('|') and not re.match(r'^\|\s*-', line)][1:]

# Every policy number below is read from the knowledge base, so a changed document changes the arithmetic.
METHOD = [('cash-on-delivery', 'wallet', 'cod_wallet'), ('cash-on-delivery', 'bank', 'cod_bank'), ('', 'upi', 'upi'),
          ('', 'card', 'card'), ('', 'net banking', 'netbanking'), ('', 'wallet', 'wallet')]
def windows():
    out = {}
    for label, time in table('REF-2'):
        low = label.lower()
        code = next(c for scope, word, c in METHOD if word in low and scope in low)
        span = re.search(r'(\d+)\s*to\s*(\d+)', time)
        out.setdefault(code, (int(span[1]), int(span[2])) if span else (0, 0))
    return out
WINDOWS = windows()
RETURN_ROWS = {re.sub(r'\s*\(.*?\)', '', label).lower(): (window, code.strip('`')) for label, window, code in table('RET-2')}
NON_RETURNABLE = {code for window, code in RETURN_ROWS.values() if 'not returnable' in window.lower()}
FEE_TEXT = section('RET-6')
PICKUP_FEE = int(need(r'reverse pickup fee of ₹\s?(\d+)', FEE_TEXT, 'RET-6')[1])
FEE_CATEGORIES = {code for label, (_, code) in RETURN_ROWS.items()
                  if label in need(r'change-of-mind returns of ([^.]+?)\.', FEE_TEXT, 'RET-6')[1].lower()}
HIGH_VALUE = int(need(r'worth more than ₹\s?([\d,]+)', section('DWM-3'), 'DWM-3')[1].replace(',', ''))
_cut = need(r'before (\d{1,2})\s*(am|pm)', section('DEL-1'), 'DEL-1')
CUTOFF_HOUR = int(_cut[1]) % 12 + (12 if _cut[2].lower() == 'pm' else 0)
ESCALATION = section('ESC-1')
LATE_DAYS = int(need(r'more than (\d+) business days past', ESCALATION, 'ESC-1')[1])
REPEAT_CONTACTS = int(need(r'escalate when it is (\d+) or more', ESCALATION, 'ESC-1')[1])
FAULTY = {'damaged', 'defective', 'wrong', 'wrong_item', 'missing_item'}

def money(x): return int(x) if abs(x - round(x)) < 0.005 else round(x, 2)

def refund_calc(items, coupon_discount=0, coupon_min_order=0, reason=None, is_plus=False, delivery_fee=0, cod_fee=0, before_shipping=False):
    """items: [{price, qty, category, return_qty}]. Applies REF-4 (coupon share and clawback), RET-6 (pickup fee), REF-5/DWM-2 (fees)."""
    subtotal = sum(i['price'] * i['qty'] for i in items)
    coupon = coupon_discount or 0
    returned = [i for i in items if i.get('return_qty')]
    if not returned: return {'error': 'Say which item and how many units are being returned.'}
    if reason == 'change_of_mind' and any(i.get('category') in NON_RETURNABLE for i in returned):
        return {'eligible': False, 'reason': 'Grocery, innerwear and digital items cannot be returned for change of mind [RET-5].'}
    gross = sum(i['price'] * i['return_qty'] for i in returned)
    own = sum(coupon * i['price'] * i['return_qty'] / subtotal for i in returned) if subtotal else 0
    kept = subtotal - gross
    clawback = coupon - own if coupon and kept > 0 and kept < (coupon_min_order or 0) else 0
    fee_possible = not is_plus and any(i.get('category') in FEE_CATEGORIES for i in returned)
    pickup = PICKUP_FEE if fee_possible and reason == 'change_of_mind' else 0
    fees = (delivery_fee or 0) + (cod_fee or 0) if reason in FAULTY or (before_shipping and kept == 0) else 0
    refund = gross - own - clawback - pickup + fees
    steps = [f'item price ₹{money(gross)}']
    if own: steps.append(f"minus its coupon share ₹{money(own)} [REF-4]")
    if clawback: steps.append(f"minus the kept items' coupon discount ₹{money(clawback)}, because the kept ₹{money(kept)} is below the ₹{money(coupon_min_order)} minimum [REF-4]")
    if pickup: steps.append(f'minus the ₹{PICKUP_FEE} reverse pickup fee for a change-of-mind fashion return [RET-6]')
    if fees: steps.append(f'plus delivery/COD fees ₹{money(fees)} [REF-5][DWM-2]')
    out = {'refund_inr': money(refund), 'steps': steps, 'coupon_share_inr': money(own), 'clawback_inr': money(clawback), 'pickup_fee_inr': pickup, 'fees_refunded_inr': money(fees)}
    if fee_possible and reason is None:
        out['note'] = f'If this is a change-of-mind return, ₹{PICKUP_FEE} reverse pickup fee is also deducted: ₹{money(refund - PICKUP_FEE)} [RET-6]. Ask the reason if unknown.'
    return out

def express_eta(placed_at):
    """DEL-1: next business day if ordered before the cutoff, otherwise the business day after."""
    when = datetime.fromisoformat(str(placed_at))
    before_cutoff = when.hour < CUTOFF_HOUR
    day = add_business_days(when.date().isoformat(), 1 if before_cutoff else 2)
    return {'expected': day.isoformat(), 'spoken_date': day.strftime('%d %B %Y'), 'ordered_before_cutoff': before_cutoff, 'cutoff_hour': CUTOFF_HOUR, 'basis': '[DEL-1]'}

def refund_status(initiated_on, method, completed_on=None, rrn=None):
    """REF-2 arrival window from initiation, how far past it today is, and whether ESC-1 #5 (>3 business days late) applies."""
    if method not in WINDOWS: return {'error': f'Unknown refund method {method!r}.'}
    lo, hi = WINDOWS[method]
    earliest, latest = add_business_days(initiated_on, lo), add_business_days(initiated_on, hi)
    out = {'initiated_on': str(initiated_on)[:10], 'method': method, 'arrives_between': [earliest.isoformat(), latest.isoformat()],
           'spoken_window': f"{earliest.strftime('%d %B %Y')} to {latest.strftime('%d %B %Y')}", 'rrn': rrn, 'basis': '[REF-2]'}
    if (lo, hi) == (0, 0): out['note'] = 'Wallet refunds are instant [REF-2].'
    if completed_on:
        return out | {'status': 'completed', 'completed_on': str(completed_on)[:10], 'escalate': False,
                      'next_step': 'Share the RRN so their bank can trace it [REF-6].' if rrn else 'No RRN on record.'}
    late = date_calc('business_days_between', latest.isoformat(), end=TODAY.isoformat())['days'] if TODAY > latest else 0
    status = 'overdue' if late > 0 else 'within_window'
    return out | {'status': status, 'business_days_past_max': late, 'escalate': late > LATE_DAYS,
                  'rule': f'Escalate only when MORE than {LATE_DAYS} business days past the maximum [ESC-1 #5].'}

def record_refund(record):
    """The refund on a verified order (return, then return-to-origin, then cancellation), if any."""
    for kind in ('return', 'rto', 'cancellation'):
        if record.get(f'{kind}_refund_initiated_on'):
            return {'kind': kind, 'initiated_on': record[f'{kind}_refund_initiated_on'], 'method': record.get(f'{kind}_refund_method'),
                    'completed_on': record.get(f'{kind}_refund_completed_on'), 'rrn': record.get(f'{kind}_rrn')}
    return None

NEGATION = re.compile(r"\b(?:not|no|never|don'?t|doesn'?t|isn'?t|wasn'?t|without)\b")
TEXT_TRIGGERS = [
    ('ESC-1 #3', 'legal action mentioned', r'consumer (?:court|forum)|legal (?:action|notice)|police (?:complaint|case)|\bFIR\b|\blawyer\b|\bsue\b|court case'),
    ('ESC-1 #7', 'product safety risk', r'(?:swell\w*|burning smell|smells? (?:like )?(?:it.s )?burning|smok(?:e|ing)|sparks?|sparking|caught fire|overheat\w*|explod\w*|electric shock)'),
    ('ESC-1 #6', 'customer asked for a human', r'(?:(?:talk|speak|connect|transfer)\w*\s+(?:me\s+)?(?:to|with)\s+(?:a\s+|an\s+|some\s+|your\s+)?(?:human|person|real person|agent|representative|manager|supervisor|someone)|human agent|real person)'),
    ('ESC-1 #2', 'activity the customer did not make',
     r"(?:order|payment|purchase|transaction|activity)s? (?:that )?I (?:didn'?t|did not|never) (?:make|place|do|authori[sz]e)|unauthori[sz]ed (?:order|payment|transaction|purchase|login|access)|(?:account|card) (?:was |got |has been )?hacked|someone (?:else )?(?:placed|logged|used my)"),
]
DAMAGE = r'damag|broke|crack|defect|wrong item|not working|dead on arrival|missing|instead of|stones?\b|shatter|dent'
STOP = {'the', 'my', 'is', 'it', 'in', 'of', 'to', 'and', 'a', 'on', 'for', 'came', 'order', 'item', 'with', 'that', 'this', 'from', 'have', 'your', 'came', 'just', 'arrived', 'inch', 'grey', 'black', 'white', 'blue', 'green', 'beige', 'maroon'}

def escalation_triggers(text, record=None):
    """ESC-1 reasons that apply now. Data rules are exact; text rules are narrow phrasings with negation guards."""
    lowered = str(text).lower(); found = []
    for rule, why, pattern in TEXT_TRIGGERS:
        for match in re.finditer(pattern, lowered, re.I):
            # "I don't need a human", "it's not swelling": a negation shortly before the phrase cancels it (not for #2, which is itself negative).
            clause = re.split(r'[,.;!?]', lowered[max(0, match.start() - 25):match.start()])[-1]
            if rule != 'ESC-1 #2' and NEGATION.search(clause): continue
            found.append({'rule': rule, 'reason': why}); break
    if record:
        if (record.get('contacts_last_7_days') or 0) >= REPEAT_CONTACTS:
            found.append({'rule': 'ESC-1 #4', 'reason': f"third or later contact within 7 days ({record['contacts_last_7_days']} earlier)"})
        refund = record_refund(record)
        if refund and refund['method'] in WINDOWS:
            status = refund_status(refund['initiated_on'], refund['method'], refund['completed_on'])
            if status['escalate']: found.append({'rule': 'ESC-1 #5', 'reason': f"refund {status['business_days_past_max']} business days past its maximum"})
        items = record.get('items') or []
        if re.search(DAMAGE, lowered) and items:
            words = {w for w in re.findall(r'[a-z0-9]{2,}', lowered) if w not in STOP}
            for item in items:
                if (item.get('unit_price_inr') or 0) <= HIGH_VALUE: continue
                # Whole title words ("tv"), or a 4+ letter part of one ("phone" in "smartphone").
                title = set(re.findall(r'[a-z0-9]+', str(item.get('title', '')).lower())) - STOP
                named = any(w in title or (len(w) >= 4 and any(w in t for t in title)) for w in words)
                reported = record.get('damage_sku') == item.get('sku')
                if named or reported or len(items) == 1:
                    found.append({'rule': 'ESC-1 #1', 'reason': f"damaged/defective/wrong item worth more than ₹{HIGH_VALUE:,}: {item.get('title')} ₹{item['unit_price_inr']:,}"})
                    break
    return found
