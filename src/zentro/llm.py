"""OpenAI-compatible chat plus native Responses function calling."""
import json
import os
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

def client():
    if not os.getenv('LLM_API_KEY') or not os.getenv('LLM_MODEL'):
        raise RuntimeError('LLM_API_KEY and LLM_MODEL are required; configure .env. No mock answers are used.')
    return OpenAI(api_key=os.environ['LLM_API_KEY'],base_url=os.getenv('LLM_BASE_URL') or None,timeout=60,max_retries=2)

def complete(messages,tools=None):
    sdk=client()
    model=os.environ['LLM_MODEL']
    mode=os.getenv('LLM_API_MODE','auto')
    if mode=='responses' or (mode=='auto' and model.startswith('gpt-6')):
        inputs=[]
        for message in messages:
            if message['role']=='tool':
                inputs.append({'type':'function_call_output','call_id':message['tool_call_id'],'output':message['content']})
            elif message.get('tool_calls'):
                if message.get('responses_output'):
                    inputs.extend(message['responses_output'])
                    continue
                if message.get('content'): inputs.append({'role':'assistant','content':message['content']})
                for call in message['tool_calls']:
                    inputs.append({'type':'function_call','call_id':call['id'],'name':call['function']['name'],'arguments':call['function']['arguments']})
            else: inputs.append({'role':message['role'],'content':message.get('content') or ''})
        args={'model':model,'input':inputs}
        # GPT-6 reasoning models do not accept temperature; other providers use chat at 0.
        if not model.startswith('gpt-6'): args['temperature']=0
        if tools:
            args['tools']=[{'type':'function',**t['function'],'strict':False} for t in tools]
            args.update(tool_choice='auto',parallel_tool_calls=False)
        response=sdk.responses.create(**args)
        calls=[{'id':item.call_id,'type':'function','function':{'name':item.name,'arguments':item.arguments}}
               for item in response.output if item.type=='function_call']
        message=ChatCompletionMessage(role='assistant',content=response.output_text,tool_calls=calls or None)
        message.responses_output=[item.model_dump(exclude_none=True) for item in response.output]
        return message
    args={'model':model,'messages':messages}
    # Reasoning models (incl. OpenRouter ids like openai/gpt-6-luna) reject temperature.
    if 'gpt-6' not in model: args['temperature']=0
    if tools: args.update(tools=tools,tool_choice='auto',parallel_tool_calls=False)
    return sdk.chat.completions.create(**args).choices[0].message

REWRITE="""Rewrite the customer's latest message as ONE short English search query for ZentroMart's support knowledge base.
The message may be noisy speech-to-text, Hindi or Hinglish. Use the conversation context to resolve references
("how long will that take?" -> what "that" is). Keep product names, SKUs, payment methods, order status and dates.
Name the support topic (e.g. return window, refund timeline, cancellation, damaged item, warranty, account security).
Do not answer the question. Output only the query."""

def rewrite_query(text,context=''):
    """LLM query rewrite for retrieval. Returns '' when disabled or unavailable so search falls back to the raw text."""
    if os.getenv('QUERY_REWRITE','1')=='0': return ''
    try:
        user=(f'Conversation so far:\n{context}\n\n' if context else '')+f'Latest customer message: {text}'
        reply=complete([{'role':'system','content':REWRITE},{'role':'user','content':user}]).content or ''
        return reply.strip().strip('"').splitlines()[0][:300] if reply.strip() else ''
    except Exception:
        return ''
