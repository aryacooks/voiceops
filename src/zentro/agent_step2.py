import json
from . import llm
from .retriever import Retriever
from .prompts import BASE, GROUNDING
from .tools_adapter import TOOLS
from .dates import date_calc
from .agent import citations, guard_reply, ungrounded, IDK

def answer(question,retriever=None):
    retriever=retriever or Retriever()
    query=llm.rewrite_query(question)
    chunks=retriever.search(question,rewrite=query) if query else retriever.search(question)
    messages=[{'role':'system','content':BASE+GROUNDING+'\nEvidence: '+json.dumps(chunks,ensure_ascii=False)},
              {'role':'user','content':question}]
    date_tools=[t for t in TOOLS if t['function']['name']=='date_calc']
    for _ in range(5):
        message=llm.complete(messages,tools=date_tools)
        if not message.tool_calls:
            raw=message.content or ''
            if ungrounded(raw,chunks): raw=IDK
            reply=guard_reply(raw,[],chunks,first=True)
            return {'reply':reply,'chunks':chunks,'rewritten_query':query,'cited_section_ids':citations(reply,chunks)}
        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            try:
                result=date_calc(**json.loads(call.function.arguments)) if call.function.name=='date_calc' else {'error':'Only date_calc is available.'}
            except (ValueError,TypeError): result={'error':'Invalid date arguments'}
            messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(result)})
    raise RuntimeError('Date tool budget exhausted')
