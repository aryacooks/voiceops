"""Gnani only. Contract checked against official SDK/REST docs 2026-10-23."""
import logging
import os
import re
import tempfile
import time
from datetime import date
from pathlib import Path
from pydub import AudioSegment, silence
from .config import TODAY

REPEAT = "Sorry, I didn't catch that. Could you say it again?"
def usable_transcript(text):
    letters=[c for c in str(text) if c.isalnum()]
    return bool(letters) and len(letters)>=2 and str(text).strip().lower() not in {'[noise]','[silence]','inaudible','unintelligible'}

def normalize_speech(text):
    text=re.sub(r'\[[A-Za-z][A-Za-z0-9_.:-]+\]','',text)
    # Ticket IDs are 35 characters; on a call, the last four are enough to quote back.
    text=re.sub(r'\b(?:ticket(?:\s+(?:ID|number|reference))?(?:\s+is)?\s+)?TKT[0-9a-f]{28}([0-9a-f]{4})\b',lambda m:('ticket number ends in ' if re.search(r'\bis\s*$',m[0][:-35]) else 'ticket ending in ')+' '.join(m[1].upper()),text,flags=re.I)
    def iso(m):
        try: return date.fromisoformat(m[0]).strftime('%d %B %Y').lstrip('0')
        except ValueError: return m[0]
    text=re.sub(r'\b\d{4}-\d{2}-\d{2}\b',iso,text)
    months='January February March April May June July August September October November December'.split()
    for month in months:
        text=re.sub(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+('+month+r')(?!\s+\d{4})\b',lambda m:m[1]+' '+m[2]+' '+str(TODAY.year),text,flags=re.I)
    text=re.sub(r'₹\s*([\d,]+(?:\.\d+)?)',r'\1 rupees',text)
    text=re.sub(r'\b(\d{4})(\d{4})\b',lambda m:' '.join(m[1])+' , '+' '.join(m[2]),text)
    text=re.sub(r'(?m)^\s*(?:[-*•]|\d+[.)])\s*','',text)
    text=re.sub(r'[*_`#]','',text)
    text=re.sub(r'\s+',' ',text)
    return re.sub(r'\s+([.,;:!?])',r'\1',text).strip()

def retry(call):
    for attempt in range(3):
        try: return call()
        except Exception as exc:
            status=getattr(exc,'status_code',None)
            if status in (400,401,403) or attempt==2: raise
            logging.warning('Gnani request failed (%s), retry %s',type(exc).__name__,attempt+1)
            time.sleep(2**attempt)

class Speech:
    def __init__(self):
        key=os.getenv('GNANI_API_KEY')
        if not key: raise RuntimeError('GNANI_API_KEY is required for Gnani STT/TTS; no speech fallback is used.')
        from gnani.stt import GnaniSTTClient
        from gnani.tts import GnaniTTSClient
        self.stt=GnaniSTTClient(api_key=key)
        self.tts=GnaniTTSClient(api_key=key)
    def transcribe(self,path):
        audio=AudioSegment.from_file(path).set_frame_rate(16000).set_channels(1).set_sample_width(2)
        # Prefer pauses near the boundary, always enforce <=55s including continuous speech.
        segments=[]
        start=0
        while start<len(audio):
            end=min(start+55000,len(audio))
            if end<len(audio):
                pauses=silence.detect_silence(audio[max(start,end-8000):end],min_silence_len=350,silence_thresh=-40)
                if pauses: end=max(start,end-8000)+pauses[-1][1]
            if end<=start: end=min(start+55000,len(audio))
            segments.append(audio[start:end]); start=end
        transcripts=[]
        with tempfile.TemporaryDirectory(prefix='zentro-stt-') as folder:
            for n,segment in enumerate(segments):
                clip=Path(folder)/f'{n}.wav'
                segment.export(clip,format='wav')
                result=retry(lambda:self.stt.transcribe(str(clip),language_code=os.getenv('STT_LANG','en-IN'),format='transcribe'))
                if result.get('success') is False: raise RuntimeError('Gnani STT returned success=False')
                transcripts.append(result.get('transcript','').strip())
        return ' '.join(filter(None,transcripts))
    def synthesize(self,text,path):
        spoken=normalize_speech(text)
        output=Path(path)
        output.parent.mkdir(parents=True,exist_ok=True)
        audio=retry(lambda:self.tts.synthesize(spoken,voice=os.getenv('TTS_VOICE','Kaveri'),
              model=os.getenv('TTS_MODEL','timbre-v2.5'),language=os.getenv('TTS_LANG','en-IN')))
        if not isinstance(audio,bytes) or not audio: raise RuntimeError('Gnani returned no audio bytes')
        output.write_bytes(audio)
        return spoken
