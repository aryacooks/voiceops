"""Local Gradio demo; the same Agent and Gnani pipeline as the grading CLI."""
import re
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import gradio as gr
from zentro.agent import Agent
from zentro.speech import Speech, usable_transcript, REPEAT
from zentro.tools_adapter import redact
from zentro.ui import CSS, EMPTY_CONVERSATION, build_theme

UNHEARD='🎙 (couldn\'t make out the audio)'

def display(reply):
    """Citations render as small source tags in the chat; the raw reply keeps them as text."""
    return re.sub(r'\[([A-Za-z][A-Za-z0-9_.:-]+)\]',r'<span class="cite">\1</span>',reply)

TYPING='<span class="typing">ZentroMart is typing…</span>'

def take_turn(message,state):
    """Echo the customer's turn at once with a typing bubble; respond() fills in the answer."""
    state=state or {'agent':None,'history':[]}
    message=message or {}
    text=(message.get('text') or '').strip()
    files=message.get('files') or []
    # Typed text wins over a stale attachment; otherwise the newest audio clip is the turn.
    audio=None if text else (files[-1] if files else None)
    if isinstance(audio,dict): audio=audio.get('path')
    state['pending']=(text,audio) if text or audio else None
    if not state['pending']: return state['history'],state,gr.skip()
    shown=redact(text) if text else '🎙 Voice message…'
    return state['history']+[{'role':'user','content':shown},{'role':'assistant','content':TYPING}],state,None

def respond(state):
    state=state or {'agent':None,'history':[]}
    if not state.get('pending'):
        return state['history'],gr.skip(),None,gr.skip(),gr.skip(),'Type a message or record one with the mic.',state
    text,audio=state.pop('pending')
    transcript=text
    spoken_path=None
    try:
        speech=Speech() if audio else None
        if audio: transcript=speech.transcribe(audio)
        if not usable_transcript(transcript): answer={'reply':REPEAT,'chunks':[],'tool_calls':[]}
        else:
            state['agent']=state['agent'] or Agent()
            answer=state['agent'].respond(transcript)
        reply=answer['reply']
        status='Reply ready.'
        if audio:
            try:
                spoken_path=str(Path(tempfile.mkdtemp(prefix='zentro-demo-'))/'reply.wav')
                speech.synthesize(reply,spoken_path)
                status='Reply ready, spoken with Gnani.'
            except Exception as exc:
                spoken_path=None;status=f'Gnani TTS failed ({type(exc).__name__}); text retained.'
        shown=state['agent'].adapter.sanitize(transcript) if state['agent'] else transcript
        user=redact(shown) if usable_transcript(shown) else UNHEARD
        if audio and usable_transcript(shown): user='🎙 '+user
        state['history'].append({'role':'user','content':user})
        state['history'].append({'role':'assistant','content':display(reply)})
        if spoken_path: state['history'].append({'role':'assistant','content':{'path':spoken_path}})
        return state['history'],redact(shown),spoken_path,answer['chunks'],answer['tool_calls'],status,state
    except Exception as exc:
        shown=state['agent'].adapter.sanitize(transcript) if state['agent'] else redact(transcript)
        return (state['history'],shown,None,getattr(exc,'retrieved_chunks',[]),getattr(exc,'tool_calls',[]),
                f'{type(exc).__name__}: {redact(str(exc))}',state)

def build_app():
    with gr.Blocks(title='ZentroMart · VoiceOps',theme=build_theme(),css=CSS) as demo:
        state=gr.State(None)
        with gr.Row(elem_id='topbar'):
            gr.HTML('<div class="brand">ZentroMart <span class="brand-detail">Voice support · AI assistant</span></div>')
            reset=gr.Button('New conversation',size='sm',elem_id='reset')
        chat=gr.Chatbot(show_label=False,type='messages',height='62vh',placeholder=EMPTY_CONVERSATION,
                        container=False,allow_tags=False,sanitize_html=True,elem_id='conversation')
        composer=gr.MultimodalTextbox(show_label=False,placeholder='Ask about an order, a return or a refund…  or tap the mic',
                                      sources=['microphone','upload'],file_types=['audio'],file_count='single',
                                      submit_btn=True,elem_id='composer')
        status=gr.Markdown('Ready.',elem_id='session-status')
        # The newest spoken reply plays on its own, like a call; it is hidden, the chat keeps a replayable copy.
        spoken=gr.Audio(type='filepath',autoplay=True,show_label=False,elem_id='autoplay')
        with gr.Accordion('Behind the scenes',open=False,elem_id='details'):
            gr.Markdown('What the agent heard, the knowledge-base chunks it retrieved, and every tool it called for the latest turn.',elem_classes='details-note')
            with gr.Row(equal_height=False):
                with gr.Column(min_width=0):
                    transcript=gr.Textbox(label='Transcript (what the agent heard)',interactive=False,lines=2,elem_id='transcript')
                    with gr.Group():
                        inspect=gr.Button('Inspect retrieval only (no LLM)',elem_id='inspect')
                        gr.Markdown('Searches the documents for whatever is typed in the message box, without generating a reply.',elem_classes='details-note')
                    calls=gr.JSON(label='Tool audit (verification details redacted)',max_height=360,elem_id='tool-calls')
                with gr.Column(min_width=0):
                    chunks=gr.JSON(label='Retrieved evidence',max_height=520,elem_id='evidence')
        gr.Markdown('Synthetic dataset · Reference date 20 October 2026 · VoiceOps 2026',elem_id='app-footer')
        def inspect_evidence(message):
            from zentro.retriever import Retriever
            question=(message or {}).get('text') or ''
            if not question.strip(): return gr.skip(),'Type a question in the box first, then inspect.'
            try: return Retriever().search(question),'Retrieved evidence only; no answer generated.'
            except Exception as exc: return [],f'Retrieval failed: {type(exc).__name__}'
        inspect.click(inspect_evidence,[composer],[chunks,status])
        composer.submit(take_turn,[composer,state],[chat,state,composer],show_progress='hidden').then(
            respond,[state],[chat,transcript,spoken,chunks,calls,status,state],show_progress='hidden')
        reset.click(lambda:([],None,'',None,[],[],'New conversation.',None),
                    outputs=[chat,composer,transcript,spoken,chunks,calls,status,state])
    return demo
if __name__=='__main__': build_app().launch(server_name='127.0.0.1',share=False)
