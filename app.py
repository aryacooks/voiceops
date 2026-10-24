"""Local Gradio demo; the same Agent and Gnani pipeline as the grading CLI."""
import base64
import html
import re
import sys
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import quote
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import gradio as gr
from zentro import inspector
from zentro.agent import Agent, citations
from zentro.speech import Speech, usable_transcript, REPEAT
from zentro.tools_adapter import redact
from zentro.ui import COMPOSER, CSS, EMPTY_CONVERSATION, HEAD, HEADER, ICONS, build_theme

# Gnani replies are served from here; launch() allows only this folder.
REPLY_DIR=Path(tempfile.gettempdir())/'zentro-replies'
TYPING='<span class="typing"><i></i><i></i><i></i></span>'
EXTENSIONS={'audio/webm':'.webm','audio/ogg':'.ogg','audio/mp4':'.m4a','audio/x-m4a':'.m4a','audio/mpeg':'.mp3',
            'audio/wav':'.wav','audio/x-wav':'.wav','audio/wave':'.wav','audio/flac':'.flac','audio/aac':'.aac'}

def save_clip(data_url):
    """Browser recordings and uploads arrive as data URLs; pydub/ffmpeg decode them for Gnani."""
    header,_,payload=data_url.partition(',')
    mime=header[5:].split(';')[0].lower()
    folder=Path(tempfile.mkdtemp(prefix='zentro-in-'))
    path=folder/('question'+EXTENSIONS.get(mime,'.webm'))
    path.write_bytes(base64.b64decode(payload))
    return str(path)

def display(reply,audio=None):
    """Reply text for the chat: escaped, citations as source tags, and a play button when Gnani spoke it."""
    text=html.escape(reply,quote=False).replace('\n','<br>')
    text=re.sub(r'\[([A-Za-z][A-Za-z0-9_.:-]+)\]',r'<span class="cite">\1</span>',text)
    if audio:
        src='/gradio_api/file='+quote(audio)
        text+=f'<br><button type="button" class="zm-play" data-src="{src}" data-autoplay="1">{ICONS["volume"]}Listen</button>'
    return text

def voice(text):
    return f'<span class="zm-vtag">{ICONS["mic"]}</span>{html.escape(text,quote=False)}'

def take_turn(text,audio,state):
    """Echo the customer's turn at once with a typing bubble; respond() fills in the answer."""
    state=state or {'agent':None,'history':[]}
    text=(text or '').strip()
    # Typed text wins over a stale clip; otherwise the recording or upload is the turn.
    audio=None if text else (audio or None)
    state['pending']=(text,audio) if text or audio else None
    if not state['pending']: return state['history'],state,'',''
    shown=html.escape(redact(text),quote=False) if text else '<span class="zm-nowrap">'+voice('Voice message…')+'</span>'
    return state['history']+[{'role':'user','content':shown},{'role':'assistant','content':TYPING}],state,'',''

def session(state):
    agent=state.get('agent')
    if not agent: return {}
    return dict(agent.adapter.public_state(),tickets=sorted(agent.adapter.tickets))

def respond(state):
    state=state or {'agent':None,'history':[]}
    if not state.get('pending'):
        return state['history'],gr.skip(),'Type a message or tap the mic.',state
    text,audio=state.pop('pending')
    transcript=text
    timings={}
    try:
        speech=None
        if audio:
            speech=Speech()
            started=time.perf_counter()
            transcript=speech.transcribe(save_clip(audio))
            timings['stt']=(time.perf_counter()-started)*1000
        started=time.perf_counter()
        if not usable_transcript(transcript): answer={'reply':REPEAT,'chunks':[],'tool_calls':[]}
        else:
            state['agent']=state['agent'] or Agent()
            answer=state['agent'].respond(transcript)
        timings['agent']=(time.perf_counter()-started)*1000
        reply=answer['reply']
        status='Reply ready.'
        spoken_path=None
        if audio:
            try:
                started=time.perf_counter()
                spoken_path=REPLY_DIR/uuid.uuid4().hex/'reply.wav'
                speech.synthesize(reply,spoken_path)
                timings['tts']=(time.perf_counter()-started)*1000
                spoken_path=str(spoken_path)
                status='Reply ready, spoken with Gnani.'
            except Exception as exc:
                spoken_path=None;status=f'Gnani TTS failed ({type(exc).__name__}); text retained.'
        shown=state['agent'].adapter.sanitize(transcript) if state['agent'] else transcript
        heard=usable_transcript(shown)
        if audio: user=voice(redact(shown)) if heard else voice("Couldn't make out the audio")
        else: user=html.escape(redact(shown),quote=False)
        state['history'].append({'role':'user','content':user})
        state['history'].append({'role':'assistant','content':display(reply,spoken_path)})
        panel=inspector.render(redact(shown) if heard else '(no usable speech)',answer['chunks'],answer['tool_calls'],
                               citations(reply,answer['chunks']),session(state),timings,status)
        return state['history'],panel,status,state
    except Exception as exc:
        shown=state['agent'].adapter.sanitize(transcript) if state['agent'] else redact(transcript)
        status=f'{type(exc).__name__}: {redact(str(exc))}'
        panel=inspector.render(shown,getattr(exc,'retrieved_chunks',[]),getattr(exc,'tool_calls',[]),(),session(state),timings,status)
        return state['history'],panel,status,state

def build_app():
    with gr.Blocks(title='ZentroMart · VoiceOps',theme=build_theme(),css=CSS,head=HEAD) as demo:
        state=gr.State(None)
        with gr.Row(elem_id='topbar'):
            gr.HTML(HEADER)
            reset=gr.Button('New chat',icon=None,size='sm',elem_id='reset')
        chat=gr.Chatbot(show_label=False,type='messages',height='calc(100vh - 290px)',min_height=360,
                        placeholder=EMPTY_CONVERSATION,container=False,sanitize_html=False,allow_tags=False,
                        elem_id='conversation')
        with gr.Column(elem_id='composer-wrap'):
            gr.HTML(COMPOSER)
            status=gr.Markdown('',elem_id='session-status')
        # The composer is custom HTML; these hidden fields carry its text or recording to Python.
        with gr.Group(elem_id='bridge'):
            bridge_text=gr.Textbox(elem_id='bridge-text',show_label=False)
            bridge_audio=gr.Textbox(elem_id='bridge-audio',show_label=False)
            bridge_send=gr.Button('send',elem_id='bridge-send')
        with gr.Accordion('Behind the scenes',open=False,elem_id='details'):
            with gr.Row(elem_id='ins-toolbar'):
                gr.HTML('<p class="ins-intro">How the latest reply was made: what the agent heard, the knowledge-base '
                        'chunks it retrieved and cited, and every tool it called. Verification details are redacted.</p>')
                inspect=gr.Button('Preview retrieval for typed text',size='sm',elem_id='inspect')
            panel=gr.HTML(inspector.render(),elem_id='inspector')
        gr.Markdown('Synthetic dataset · Reference date 20 October 2026 · VoiceOps 2026',elem_id='app-footer')
        def inspect_evidence(question):
            from zentro.retriever import Retriever
            if not (question or '').strip(): return gr.skip(),'Type a question in the message box first, then preview retrieval.'
            try:
                found=Retriever().search(question)
                return inspector.render(question,found,inspect_only=True,status='Retrieval only; no answer generated'),'Retrieval preview ready.'
            except Exception as exc: return gr.skip(),f'Retrieval failed: {type(exc).__name__}'
        inspect.click(inspect_evidence,[bridge_text],[panel,status],js="() => [document.querySelector('#zm-input').value]")
        bridge_send.click(take_turn,[bridge_text,bridge_audio,state],[chat,state,bridge_text,bridge_audio],show_progress='hidden').then(
            respond,[state],[chat,panel,status,state],show_progress='hidden')
        reset.click(lambda:([],inspector.render(),'',None),outputs=[chat,panel,status,state])
    return demo
if __name__=='__main__':
    REPLY_DIR.mkdir(parents=True,exist_ok=True)
    build_app().launch(server_name='127.0.0.1',share=False,allowed_paths=[str(REPLY_DIR)])
