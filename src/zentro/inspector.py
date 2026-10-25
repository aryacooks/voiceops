"""Presentation-only: renders one turn's transcript, evidence and tool audit as HTML for the demo's inspector."""
import html
import json
import re

DOC_TYPES={'pol':('Policy','policy'),'agent':('Agent guide','guide'),'help':('Help','help'),'faq':('FAQ','faq'),
           'mkt':('Marketing','mkt'),'meta':('KB rules','meta'),'catalog':('Catalog','catalog')}
TOOL_LABELS={'search_kb':'Searched knowledge base','lookup_order':'Order lookup','create_ticket':'Human handover ticket',
             'date_calc':'Date calculation','catalog_lookup':'Catalog lookup','is_pincode_serviceable':'Pincode check',
             'refund_calc':'Refund calculation','express_eta':'Express arrival date','refund_status':'Refund status'}

def esc(value): return html.escape(str(value),quote=True)

def stat(label,value,tone=''):
    return f'<div class="ins-stat {tone}"><span>{esc(label)}</span><b>{esc(value)}</b></div>'

def seconds(ms): return f'{ms/1000:.1f}s' if ms is not None else '–'

def tool_result(name,args,result):
    """One plain-English line per tool result; raw payloads stay in the raw-data section."""
    result=result or {}
    if result.get('error'): return 'Error: '+str(result['error']),'bad'
    if name=='search_kb':
        ids=result.get('section_ids',[])
        return (f'{len(ids)} chunks: '+', '.join(ids)) if ids else 'No chunks found','muted'
    if name=='lookup_order':
        if result.get('locked'): return 'Locked after two failed checks; no order details shared','bad'
        if result.get('verified'): return 'Caller verified, order details unlocked','ok'
        if result.get('verification_required') and not (args.get('phone_last4') or args.get('pincode')):
            return 'Order found; asked the caller for a verification detail','muted'
        if result.get('verification_required'): return 'Verification detail did not match','bad'
        return json.dumps(result,ensure_ascii=False)[:160],'muted'
    if name=='create_ticket':
        if result.get('uncertain'): return 'Timed out; the ticket may or may not have been saved','warn'
        return (f'Ticket created: {result.get("ticket_id")}','ok') if result.get('created') else ('Ticket not created','bad')
    if name=='refund_calc':
        if result.get('eligible') is False: return 'Not eligible: '+str(result.get('reason','')),'bad'
        if 'refund_inr' in result: return f'Refund ₹{result["refund_inr"]:,}'+(' · '+result['note'] if result.get('note') else ''),'ok'
    if name=='express_eta' and result.get('spoken_date'): return 'Expected '+result['spoken_date'],'ok'
    if name=='refund_status' and result.get('status'):
        late=f', {result["business_days_past_max"]} business days past the maximum' if result.get('business_days_past_max') else ''
        window=f' · due {result["spoken_window"]}' if result.get('spoken_window') else ''
        return f'{result["status"].replace("_"," ").capitalize()}{late}{window}'+(' · escalate' if result.get('escalate') else ''),'bad' if result.get('escalate') else 'ok'
    if name=='date_calc':
        if 'spoken_date' in result: return result['spoken_date'],'ok'
        if 'days' in result: return f'{result["days"]} days','ok'
        return result.get('date',''),'ok'
    if name=='catalog_lookup':
        rows=result.get('products',[])
        return ('; '.join(f'{r.get("sku")} · {r.get("return_category")} · warranty {r.get("warranty_months")} mo' for r in rows) or 'No product found'),'muted'
    if name=='is_pincode_serviceable':
        return ', '.join(f'{k}: {v}' for k,v in result.items()),'muted'
    return json.dumps(result,ensure_ascii=False)[:160],'muted'

def tool_args(name,args):
    if name=='search_kb':
        parts=[f'“{args.get("query","")}”']
        if args.get('rewritten_query'): parts.append(f'rewritten → “{args["rewritten_query"]}”')
        return ' '.join(parts)
    return ', '.join(f'{k}: {v}' for k,v in (args or {}).items())

def evidence_card(chunk,cited,top):
    label,tone=DOC_TYPES.get(chunk.get('doc_type'),(chunk.get('doc_type','Source'),'meta'))
    score=float(chunk.get('score') or 0)
    width=max(6,min(100,round(score/top*100))) if top else 6
    status=chunk.get('status','')
    text=chunk.get('text','')
    lines=text.split('\n',2)
    body=lines[-1] if len(lines)>2 else text
    flags=[f'<span class="ins-type {tone}">{esc(label)}</span>']
    if status=='superseded': flags.append('<span class="ins-flag warn">Superseded</span>')
    if cited: flags.append('<span class="ins-flag ok">Cited in reply</span>')
    meta=' · '.join(x for x in (chunk.get('doc',''),('effective '+chunk['effective_from']) if chunk.get('effective_from') else '') if x)
    return f"""
<details class="ins-card{' cited' if cited else ''}">
  <summary>
    <span class="ins-sid">{esc(chunk.get('section_id',''))}</span>
    <span class="ins-title">{esc(lines[1] if len(lines)>2 and lines[1].strip() else lines[0])}</span>
    <span class="ins-flags">{''.join(flags)}</span>
    <span class="ins-score" title="Retrieval relevance {score:.4f} (rank fusion score, not confidence)"><i style="width:{width}%"></i></span>
  </summary>
  <div class="ins-meta">{esc(meta)} · relevance {score:.4f} (retrieval rank score, not confidence)</div>
  <div class="ins-text">{esc(body)}</div>
</details>"""

def render(transcript='',chunks=(),calls=(),cited=(),state=None,timings=None,status='',inspect_only=False):
    """Inspector HTML for the latest turn; empty arguments render the placeholder."""
    if not transcript and not chunks and not calls:
        return ('<div class="ins-empty">Send a message and this panel shows what the agent heard, which knowledge-base '
                'chunks it retrieved and cited, and every tool it called.</div>')
    chunks=list(chunks or []); calls=list(calls or []); cited=set(cited or [])
    timings=timings or {}
    state=state or {}
    rewrite=next((c['arguments'].get('rewritten_query') for c in calls if c['name']=='search_kb' and c.get('arguments',{}).get('rewritten_query')),'')
    used=[c for c in calls if not (c['name']=='search_kb' and c is calls[0])]
    auto=' (the first is the automatic retrieval)' if len(used)<len(calls) else ''
    verified='Verified' if state.get('verified') else ('Not verified' if state.get('order_id') else 'No order')
    stats=''.join([
        stat('Chunks retrieved',len(chunks)),
        stat('Speech to text',seconds(timings.get('stt'))) if timings.get('stt') is not None else '',
        stat('Agent',seconds(timings.get('agent'))),
        stat('Text to speech',seconds(timings.get('tts'))) if timings.get('tts') is not None else '',
        stat('Sources cited',len(cited),'ok' if cited else ''),
        stat('Agent tool calls',len(used)),
        stat('Caller',verified,'ok' if state.get('verified') else ''),
    ])
    top=max([float(c.get('score') or 0) for c in chunks] or [0])
    ordered=sorted(chunks,key=lambda c:(c.get('section_id') not in cited,-(float(c.get('score') or 0))))
    cards=''.join(evidence_card(c,c.get('section_id') in cited,top) for c in ordered) or '<p class="ins-none">No chunks retrieved.</p>'
    steps=''.join(f"""
<li class="ins-step {tone}">
  <span class="ins-dot"></span>
  <div><b>{esc(TOOL_LABELS.get(c['name'],c['name']))}</b><code>{esc(c['name'])}</code>
  <p class="ins-args">{esc(tool_args(c['name'],c.get('arguments',{})))}</p>
  <p class="ins-res">{esc(line)}</p>
  <details class="ins-full"><summary>Arguments and full result</summary><pre>{esc(json.dumps({'arguments':c.get('arguments',{}),'result':c.get('result')},ensure_ascii=False,indent=2))}</pre></details></div>
</li>""" for c in calls for line,tone in [tool_result(c['name'],c.get('arguments',{}),c.get('result'))])
    # Speech steps appear only when the turn really ran them (their timings were recorded).
    if timings.get('stt') is not None:
        steps=f'<li class="ins-step ok"><span class="ins-dot"></span><div><b>Speech transcribed</b><code>Gnani STT</code><p class="ins-res">{seconds(timings["stt"])}</p></div></li>'+steps
    if timings.get('tts') is not None:
        steps+=f'<li class="ins-step ok"><span class="ins-dot"></span><div><b>Reply spoken</b><code>Gnani TTS</code><p class="ins-res">{seconds(timings["tts"])}</p></div></li>'
    ticket=', '.join(state.get('tickets',[]))
    session=''.join([
        f'<div><span>Order</span><b>{esc(state.get("order_id") or "–")}</b></div>',
        f'<div><span>Verification</span><b>{esc(verified)}</b></div>',
        f'<div><span>Failed checks</span><b>{esc(state.get("verification_failures",0))}</b></div>',
        f'<div><span>Tickets</span><b>{esc(ticket or "–")}</b></div>',
    ])
    raw=json.dumps({'retrieved_chunks':chunks,'tool_calls':calls},ensure_ascii=False,indent=2)
    heading='Retrieval preview (no answer generated)' if inspect_only else 'Latest turn'
    heard=f'<p class="ins-heard">“{esc(transcript)}”</p>' if transcript else ''
    rewritten=f'<p class="ins-rewrite"><span>Search query</span>{esc(rewrite)}</p>' if rewrite else ''
    return f"""
<div class="ins">
  <div class="ins-head"><span class="ins-kicker{' preview' if inspect_only else ''}">{esc(heading)}</span>{f'<span class="ins-status">{esc(status)}</span>' if status else ''}</div>
  {'<p class="ins-note">Retrieval only: these are the chunks the search returns for the typed text. No answer was generated and no tools ran.</p>' if inspect_only else ''}
  {'' if inspect_only else f'<div class="ins-stats">{stats}</div>'}
  <section><h4>What the agent heard</h4>{heard or '<p class="ins-none">–</p>'}{rewritten}</section>
  {'' if inspect_only else f'<section><h4>Activity <small>{len(calls)} tool calls, in the order they ran{auto}</small></h4><ol class="ins-steps">{steps}</ol></section>'}
  <section><h4>Evidence <small>{len(chunks)} retrieved · {len(cited)} cited · tap a card to read it</small></h4><div class="ins-cards">{cards}</div></section>
  {'' if inspect_only else f'<section><h4>Session</h4><div class="ins-session">{session}</div></section>'}
  <details class="ins-raw"><summary>Raw data (JSON)</summary><pre>{esc(raw)}</pre></details>
</div>"""
