"""Local Gradio demo; the same Agent and Gnani pipeline as the grading CLI."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import gradio as gr
from zentro.agent import Agent
from zentro.speech import Speech, normalize_speech, usable_transcript, REPEAT
from zentro.tools_adapter import redact
from zentro.ui import CSS, EMPTY_CONVERSATION, build_theme

def respond(audio,text,state):
    state=state or {'agent':None,'history':[]}
    transcript=text or ''
    spoken_path=None
    try:
        if text and text.strip(): audio=None
        speech=Speech() if audio else None
        if audio: transcript=speech.transcribe(audio)
        if not usable_transcript(transcript): answer={'reply':REPEAT,'chunks':[],'tool_calls':[]}
        else:
            state['agent']=state['agent'] or Agent()
            answer=state['agent'].respond(transcript)
        reply=answer['reply']
        status='Text response ready.'
        if audio:
            try:
                folder=Path(tempfile.mkdtemp(prefix='zentro-demo-'))
                spoken_path=str(folder/'reply.wav')
                speech.synthesize(reply,spoken_path)
                status='Gnani audio response ready.'
            except Exception as exc:
                spoken_path=None;status=f'Gnani TTS failed ({type(exc).__name__}); text retained.'
        transcript=state['agent'].adapter.sanitize(transcript) if state['agent'] else transcript
        state['history'] += [{'role':'user','content':redact(transcript)},{'role':'assistant','content':reply}]
        return state['history'],redact(transcript),spoken_path,answer['chunks'],answer['tool_calls'],status,state
    except Exception as exc:
        transcript=state['agent'].adapter.sanitize(transcript) if state['agent'] else redact(transcript)
        return state['history'],transcript,None,getattr(exc,'retrieved_chunks',[]),getattr(exc,'tool_calls',[]),f'{type(exc).__name__}: {redact(str(exc))}',state

def build_app():
    with gr.Blocks(title='ZentroMart · VoiceOps',theme=build_theme(),css=CSS) as demo:
        gr.HTML('<div class="brandbar"><div class="brand">ZentroMart</div><div class="brand-detail">Voice support</div></div>',elem_id='topbar')
        gr.HTML('<h1>How can we help?</h1><p>Speak or type. Get answers grounded in ZentroMart policy.</p>',elem_id='intro')
        state=gr.State(None)
        with gr.Row(elem_id='workspace'):
            with gr.Column(scale=7,min_width=0,elem_id='conversation-panel'):
                with gr.Row(elem_id='conversation-heading'):
                    gr.HTML('<h2 class="panel-title">Conversation</h2>')
                    reset=gr.Button('New conversation',size='sm',elem_id='reset')
                chat=gr.Chatbot(label='Conversation',show_label=False,type='messages',height=300,
                                placeholder=EMPTY_CONVERSATION,container=False,allow_tags=False,
                                elem_id='conversation')
                with gr.Row(elem_id='composer'):
                    text=gr.Textbox(label='Or type a question',placeholder='How fast are refunds to the ZentroMart Wallet?',
                                    lines=2,max_lines=4,scale=1,min_width=0,elem_id='message-input')
                    send=gr.Button('Ask ZentroMart',variant='primary',scale=0,elem_id='send')
                with gr.Accordion('Record or upload a question',open=False,elem_id='voice-input'):
                    audio=gr.Audio(sources=['microphone','upload'],type='filepath',show_label=False,
                                   label='Record or upload a question',elem_id='microphone')
            with gr.Column(scale=4,min_width=0,elem_id='session-panel'):
                gr.HTML('<h2 class="panel-title">Session details</h2>')
                transcript=gr.Textbox(label='Transcript',interactive=False,lines=2,placeholder='Your message appears here.',elem_id='transcript')
                spoken=gr.Audio(label='Gnani reply',type='filepath',elem_id='reply-audio')
                status=gr.Textbox(label='Status',interactive=False,lines=2,
                                  value='Ready. Configure .env before making LLM or voice calls.',elem_id='session-status')
                with gr.Accordion('Retrieved evidence',open=False,elem_classes='detail-disclosure') as evidence_panel:
                    chunks=gr.JSON(label='Chunks',show_label=False,max_height=320,elem_id='evidence')
                with gr.Accordion('Tool audit',open=False,elem_classes='detail-disclosure'):
                    calls=gr.JSON(label='Calls (verification details redacted)',show_label=False,max_height=320,elem_id='tool-calls')
                inspect=gr.Button('Inspect retrieval only (no LLM)',elem_id='inspect')
                gr.Markdown('Search source documents without generating a reply.',elem_id='inspect-note')
        gr.Markdown('Synthetic dataset · Reference date 20 October 2026 · VoiceOps 2026',elem_id='app-footer')
        def inspect_evidence(question):
            from zentro.retriever import Retriever
            try: return Retriever().search(question),'Retrieved evidence only; no answer generated.'
            except Exception as exc: return [],f'Retrieval failed: {type(exc).__name__}'
        inspect.click(inspect_evidence,[text],[chunks,status]).then(lambda:gr.update(open=True),outputs=[evidence_panel])
        send.click(respond,[audio,text,state],[chat,transcript,spoken,chunks,calls,status,state]).then(lambda:('',None),outputs=[text,audio])
        text.submit(respond,[audio,text,state],[chat,transcript,spoken,chunks,calls,status,state]).then(lambda:('',None),outputs=[text,audio])
        reset.click(lambda:([],None,'','',None,[],[],'New conversation.',None),outputs=[chat,audio,text,transcript,spoken,chunks,calls,status,state]).then(lambda:gr.update(open=False),outputs=[evidence_panel])
    return demo
if __name__=='__main__': build_app().launch(server_name='127.0.0.1',share=False)
