"""Presentation-only Gradio theme: cream canvas, white surfaces, ink and brown."""
import gradio as gr


def build_theme():
    theme = gr.themes.Base(
        primary_hue="stone", secondary_hue="stone", neutral_hue="stone",
        font=["Helvetica Neue", "Arial", "sans-serif"],
        font_mono=["SFMono-Regular", "Consolas", "monospace"],
        radius_size="sm", spacing_size="md",
    )
    # Keep the requested cream appearance consistent with browser theme settings.
    paired = {
        "body_background_fill": "#f4f0e9",
        "body_text_color": "#211e1b",
        "body_text_color_subdued": "#756b62",
        "background_fill_primary": "#ffffff",
        "background_fill_secondary": "#f8f5f0",
        "block_background_fill": "#ffffff",
        "block_border_color": "#e3dcd2",
        "block_label_background_fill": "transparent",
        "block_label_text_color": "#65584c",
        "block_title_text_color": "#211e1b",
        "border_color_primary": "#e3dcd2",
        "border_color_accent": "#7b5d47",
        "border_color_accent_subdued": "#e3dcd2",
        "panel_background_fill": "#ffffff",
        "panel_border_color": "#e3dcd2",
        "input_background_fill": "#f8f5f0",
        "input_background_fill_focus": "#ffffff",
        "input_background_fill_hover": "#f8f5f0",
        "input_border_color": "#ddd5ca",
        "input_border_color_focus": "#7b5d47",
        "input_border_color_hover": "#b9ab9b",
        "input_placeholder_color": "#75695d",
        "button_primary_background_fill": "#211e1b",
        "button_primary_background_fill_hover": "#674c38",
        "button_primary_border_color": "#211e1b",
        "button_primary_border_color_hover": "#674c38",
        "button_primary_text_color": "#ffffff",
        "button_primary_text_color_hover": "#ffffff",
        "button_secondary_background_fill": "#ffffff",
        "button_secondary_background_fill_hover": "#eee7dd",
        "button_secondary_border_color": "#ddd5ca",
        "button_secondary_border_color_hover": "#b9ab9b",
        "button_secondary_text_color": "#45392e",
        "button_secondary_text_color_hover": "#211e1b",
        "link_text_color": "#674c38",
        "link_text_color_hover": "#211e1b",
        "accordion_text_color": "#45392e",
        "code_background_fill": "#f8f5f0",
        "loader_color": "#7b5d47",
        "slider_color": "#7b5d47",
        "error_background_fill": "#f5ede3",
        "error_border_color": "#b79b7b",
        "error_text_color": "#63422d",
    }
    tokens = {key: value for name, value in paired.items() for key in (name, name + "_dark")}
    return theme.set(
        **tokens, color_accent="#7b5d47", color_accent_soft="#eee7dd",
        color_accent_soft_dark="#eee7dd", block_border_width="0px",
        block_border_width_dark="0px", block_shadow="none", block_shadow_dark="none",
        block_label_shadow="none", block_padding="0px", block_radius="0px",
        block_label_padding="0px", block_label_margin="0 0 8px 0",
        block_label_text_size="12px", block_label_text_weight="500",
        input_radius="6px", input_shadow="none", input_shadow_dark="none",
        input_shadow_focus="none", input_shadow_focus_dark="none",
        button_primary_shadow="none", button_primary_shadow_hover="none",
        button_primary_shadow_active="none", button_primary_shadow_dark="none",
        button_secondary_shadow="none", button_secondary_shadow_dark="none",
        button_large_radius="6px", button_small_radius="6px",
        button_large_text_size="14px", button_large_text_weight="500",
        button_transition="background-color 150ms ease, border-color 150ms ease",
        layout_gap="16px", form_gap_width="16px",
    )


def svg(body, view="0 0 24 24", cls=""):
    return (f'<svg class="zm-icon {cls}" viewBox="{view}" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


# Paths from the Its Hover icon set (itshover.com); its React/motion hover animations are recreated in CSS.
# The set has no microphone or stop glyph, so those two use the Tabler outlines it is drawn from.
ICONS = {
    "send": svg('<g class="ih-plane"><path d="M3.714 3.048a.498.498 0 0 0-.683.627l2.843 7.627a2 2 0 0 1 0 1.396l-2.842 7.627a.498.498 0 0 0 .682.627l18-8.5a.5.5 0 0 0 0-.904z"/><path d="M6 12h16"/></g>'),
    "upload": svg('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><g class="ih-arrow"><path d="M12 3v12"/><path d="m17 8-5-5-5 5"/></g>'),
    "refresh": svg('<g class="ih-spin"><path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4"/><path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"/></g>'),
    "volume": svg('<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><path class="ih-wave1" d="M16 9a5 5 0 0 1 0 6"/><path class="ih-wave2" d="M19.364 18.364a9 9 0 0 0 0-12.728"/>'),
    "x": svg('<g class="ih-x"><path d="M18 6l-12 12"/><path d="M6 6l12 12"/></g>'),
    "sparkles": svg('<path class="ih-spark-s" d="M16 18a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2z"/><path class="ih-spark-s" d="M16 6a2 2 0 0 1 2 2a2 2 0 0 1 2 -2a2 2 0 0 1 -2 -2a2 2 0 0 1 -2 2z"/><path class="ih-spark" d="M9 18a6 6 0 0 1 6 -6a6 6 0 0 1 -6 -6a6 6 0 0 1 -6 6a6 6 0 0 1 6 6z"/>'),
    "cart": svg('<path d="M8.49994 10H41L37.569 21.4367C36.9345 23.5517 34.9879 25 32.7798 25H10.4999"/><path d="M11 45C13.2091 45 15 43.2091 15 41C15 38.7909 13.2091 37 11 37C8.79086 37 7 38.7909 7 41C7 43.2091 8.79086 45 11 45Z"/><path d="M37 45C39.2091 45 41 43.2091 41 41C41 38.7909 39.2091 37 37 37C34.7909 37 33 38.7909 33 41C33 43.2091 34.7909 45 37 45Z"/><path d="M41 32H9.46174C7.17727 32 6.08953 29.1885 7.77914 27.651L10.6923 25L7.81067 5.14103C7.63231 3.91188 6.57863 3.00005 5.33661 3.00003L3 3"/><g class="ih-items"><path d="M30 16L30 19"/><path d="M24 16L24 19"/><path d="M18 16L18 19"/></g>', view="0 0 48 48"),
    "mic": svg('<path d="M9 5a3 3 0 0 1 3 -3a3 3 0 0 1 3 3v5a3 3 0 0 1 -3 3a3 3 0 0 1 -3 -3z"/><path d="M5 10a7 7 0 0 0 14 0"/><path d="M8 21l8 0"/><path d="M12 17l0 4"/>'),
    "stop": svg('<rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none"/>'),
}


HEADER = f"""
<div class="zm-brand">
  <span class="zm-logo">{ICONS['cart']}</span>
  <span><span class="zm-name">ZentroMart</span><span class="zm-sub">{ICONS['sparkles']} AI support assistant · speak or type</span></span>
</div>
"""


COMPOSER = f"""
<div id="zm-composer">
  <div class="zm-type">
    <button type="button" class="zm-btn ghost" id="zm-upload" title="Upload an audio file" aria-label="Upload an audio file">{ICONS['upload']}</button>
    <input type="file" id="zm-file" accept="audio/*" hidden>
    <textarea id="zm-input" rows="1" placeholder="Ask about an order, a return or a refund…" aria-label="Message"></textarea>
    <button type="button" class="zm-btn primary" id="zm-mic" title="Speak your question" aria-label="Record a voice message">{ICONS['mic']}</button>
    <button type="button" class="zm-btn primary" id="zm-send" title="Send" aria-label="Send message">{ICONS['send']}</button>
  </div>
  <div class="zm-rec" aria-live="polite">
    <button type="button" class="zm-btn ghost" id="zm-cancel" title="Discard recording" aria-label="Discard recording">{ICONS['x']}</button>
    <span class="zm-dot"></span>
    <span id="zm-timer">0:00</span>
    <div id="zm-wave"></div>
    <span id="zm-hint">Listening…</span>
    <button type="button" class="zm-btn primary" id="zm-stop" title="Stop and send" aria-label="Stop and send">{ICONS['send']}</button>
  </div>
</div>
<p id="zm-note">Enter to send · Shift+Enter for a new line · tap the mic, speak, then tap send</p>
"""


# Gradio does not run <script> inside gr.HTML, so the composer logic is injected through Blocks(head=...).
HEAD = """
<script>
(() => {
  const $ = s => document.querySelector(s);
  const MAX_SECONDS = 55;
  let rec = null, stream = null, chunks = [], cancelled = false, started = 0;
  let timer = null, raf = null, ctx = null, loudest = 0, busy = false, sawTyping = false, busyTimer = null;
  const played = new Set();
  const player = new Audio();

  function status(text) {
    const box = $('#session-status');
    if (box) box.querySelector('p') ? box.querySelector('p').textContent = text : box.textContent = text;
  }
  function setBridge(id, value) {
    const el = document.querySelector(`#${id} textarea, #${id} input`);
    if (!el) return;
    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }
  function setBusy(on) {
    busy = on; sawTyping = false;
    $('#zm-composer')?.classList.toggle('busy', on);
    clearTimeout(busyTimer);
    if (on) busyTimer = setTimeout(() => setBusy(false), 90000);
  }
  function fire(text, audio) {
    if (busy) return;
    setBridge('bridge-text', text || '');
    setBridge('bridge-audio', audio || '');
    setBusy(true);
    setTimeout(() => $('#bridge-send')?.click(), 80);
  }
  function autosize(t) {
    t.style.height = 'auto';
    t.style.height = Math.min(t.scrollHeight, 160) + 'px';
    t.style.overflowY = t.scrollHeight > 160 ? 'auto' : 'hidden';
  }
  function syncMode() {
    const t = $('#zm-input');
    $('#zm-composer')?.classList.toggle('has-text', !!(t && t.value.trim()));
  }
  function sendText() {
    const t = $('#zm-input');
    const v = t.value.trim();
    if (!v || busy) return;
    fire(v, '');
    t.value = ''; autosize(t); syncMode();
  }

  // Recording: browser MediaRecorder, sent to Python as a data URL; Gnani does the transcription.
  async function startRec() {
    if (busy) return;
    if (!navigator.mediaDevices || !window.MediaRecorder) { status('This browser cannot record audio; type instead or upload a file.'); return; }
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    } catch (err) {
      status('Microphone blocked. Allow mic access from the address bar, then try again.'); return;
    }
    const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'].find(m => MediaRecorder.isTypeSupported(m)) || '';
    rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    chunks = []; cancelled = false; loudest = 0;
    rec.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
    rec.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      stopMeter(); setRecording(false);
      if (cancelled || !chunks.length) { status('Recording discarded.'); return; }
      const blob = new Blob(chunks, { type: rec.mimeType || 'audio/webm' });
      const reader = new FileReader();
      reader.onload = () => fire('', reader.result);
      reader.readAsDataURL(blob);
    };
    rec.start(250); started = Date.now();
    setRecording(true); startMeter();
  }
  function stopRec(discard) {
    cancelled = !!discard;
    if (rec && rec.state !== 'inactive') rec.stop();
  }
  function setRecording(on) {
    $('#zm-composer')?.classList.toggle('recording', on);
    clearInterval(timer);
    if (!on) return;
    $('#zm-wave').innerHTML = '';
    $('#zm-hint').textContent = 'Listening…';
    timer = setInterval(() => {
      const s = Math.floor((Date.now() - started) / 1000);
      $('#zm-timer').textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
      if (s >= 2 && loudest < 0.02) $('#zm-hint').textContent = "Can't hear you. Move closer or check your mic.";
      else if (loudest >= 0.02) $('#zm-hint').textContent = 'Tap send when you finish';
      if (s >= MAX_SECONDS) stopRec(false);
    }, 250);
  }
  function startMeter() {
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      ctx.createMediaStreamSource(stream).connect(analyser);
      const data = new Uint8Array(analyser.fftSize);
      const wave = $('#zm-wave');
      let last = 0;
      const draw = now => {
        raf = requestAnimationFrame(draw);
        if (now - last < 90) return;
        last = now;
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (const v of data) sum += ((v - 128) / 128) ** 2;
        const rms = Math.sqrt(sum / data.length);
        loudest = Math.max(loudest, rms);
        const bar = document.createElement('i');
        bar.style.height = Math.max(3, Math.min(26, rms * 160)) + 'px';
        wave.appendChild(bar);
        while (wave.children.length > 48) wave.firstChild.remove();
      };
      raf = requestAnimationFrame(draw);
    } catch (e) { /* the level meter is optional */ }
  }
  function stopMeter() { cancelAnimationFrame(raf); if (ctx) ctx.close(); ctx = null; }

  // Spoken replies: one shared player, newest reply plays on its own.
  function play(btn) {
    const src = btn.dataset.src;
    document.querySelectorAll('.zm-play.playing').forEach(b => b.classList.remove('playing'));
    if (!player.paused && player.dataset.src === src) { player.pause(); return; }
    player.src = src; player.dataset.src = src;
    player.play().then(() => btn.classList.add('playing')).catch(() => {});
    player.onended = player.onpause = () => btn.classList.remove('playing');
  }

  document.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.id === 'zm-send') sendText();
    else if (b.id === 'zm-mic') startRec();
    else if (b.id === 'zm-stop') stopRec(false);
    else if (b.id === 'zm-cancel') stopRec(true);
    else if (b.id === 'zm-upload') $('#zm-file')?.click();
    else if (b.classList.contains('zm-play')) play(b);
    else if (b.id === 'reset') { const t = $('#zm-input'); if (t) { t.value = ''; autosize(t); syncMode(); } player.pause(); played.clear(); setBusy(false); }
  });
  document.addEventListener('keydown', e => {
    if (e.target.id === 'zm-input' && e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendText(); }
  });
  document.addEventListener('input', e => {
    if (e.target.id === 'zm-input') { autosize(e.target); syncMode(); }
  });
  document.addEventListener('change', e => {
    if (e.target.id !== 'zm-file' || !e.target.files.length) return;
    const file = e.target.files[0];
    e.target.value = '';
    if (file.size > 15 * 1024 * 1024) { status('That file is over 15 MB; keep questions under a minute.'); return; }
    const reader = new FileReader();
    reader.onload = () => fire('', reader.result);
    reader.readAsDataURL(file);
  });
  new MutationObserver(() => {
    const typing = document.querySelector('#conversation .typing');
    if (typing) sawTyping = true;
    else if (busy && sawTyping) setBusy(false);
    const buttons = document.querySelectorAll('#conversation .zm-play[data-autoplay="1"]');
    const newest = buttons[buttons.length - 1];
    if (newest && !played.has(newest.dataset.src)) { played.add(newest.dataset.src); play(newest); }
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
</script>
"""


CSS = """
:root, body, .dark { color-scheme: light; background: #f4f0e9 !important; }
body { margin: 0; -webkit-font-smoothing: antialiased; }
.gradio-container {
    width: 100% !important; max-width: 820px !important;
    margin: 0 auto !important; padding: 0 20px 24px !important;
    font-family: 'Helvetica Neue', Arial, sans-serif !important;
    color: #211e1b !important; background: #f4f0e9 !important;
}
.gradio-container footer { display: none !important; }
.gradio-container .form { border: 0 !important; box-shadow: none !important; background: transparent !important; }
.gradio-container button, .gradio-container textarea { font-family: inherit !important; }
.gradio-container button { box-shadow: none !important; }
.gradio-container button:focus-visible, .gradio-container textarea:focus-visible {
    outline: 2px solid #7b5d47 !important; outline-offset: 2px !important;
}
.gradio-container label > span { background: transparent !important; }
.zm-icon { width: 20px; height: 20px; flex: none; overflow: visible; }
/* Gradio's .prose * rule recolours everything inside gr.HTML; icons follow their own control instead. */
.zm-btn *, .zm-logo *, .zm-play *, .zm-sub *, .empty-mark *, .zm-vtag * { color: inherit !important; }

/* Header */
#topbar { position: sticky; top: 0; z-index: 5; align-items: center; justify-content: space-between; flex-wrap: nowrap; gap: 12px;
    padding: 14px 0 12px; border-bottom: 1px solid #e3dcd2; background: #f4f0e9; }
#topbar > div { min-width: 0; }
.zm-brand { display: flex; align-items: center; gap: 12px; }
.zm-logo { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 12px; background: #211e1b; color: #fbf8f3; }
.zm-logo .zm-icon { width: 22px; height: 22px; stroke-width: 2.6; }
.zm-name { display: block; font-size: 17px; font-weight: 650; letter-spacing: -.4px; line-height: 1.2; }
.zm-sub { display: flex; align-items: center; gap: 4px; color: #7d6f62; font-size: 12px; margin-top: 2px; }
.zm-sub .zm-icon { width: 13px; height: 13px; color: #a3825f; }
#reset { flex: 0 0 auto; width: auto !important; min-width: 0 !important; padding: 7px 12px !important; font-size: 12px !important;
    border-radius: 999px !important; display: inline-flex; gap: 6px; align-items: center; }

/* Conversation */
#conversation { background: transparent !important; border: 0 !important; padding: 4px 0 0 !important; }
#conversation .bubble-wrap { padding: 12px 2px !important; background: transparent !important; }
#conversation .placeholder-content { padding: 20px; }
#conversation .top-panel, #conversation .icon-button-wrapper.top-panel { display: none !important; }
#conversation .avatar-container { display: none !important; }
#conversation .message-row { margin: 3px 0 !important; }
#conversation .message { font-size: 15px !important; line-height: 1.6 !important; border-radius: 18px !important;
    box-shadow: none !important; padding: 10px 15px !important; max-width: 80%; }
#conversation .message p { margin: 0 !important; }
#conversation .user { background: #211e1b !important; border: 0 !important; border-bottom-right-radius: 6px !important; }
#conversation .user, #conversation .user * { color: #fbf8f3 !important; }
#conversation .bot { background: #ffffff !important; color: #211e1b !important; border: 1px solid #e7e0d6 !important;
    border-bottom-left-radius: 6px !important; }
.zm-nowrap { white-space: nowrap; }
.zm-vtag { display: inline-flex; vertical-align: -3px; margin-right: 4px; opacity: .75; }
.zm-vtag .zm-icon { width: 15px; height: 15px; }
.cite { display: inline-block; margin: 0 1px; padding: 0 7px; border-radius: 999px; background: #f1ebe2;
    color: #7a5d45; font-size: 11px; font-weight: 550; line-height: 18px; vertical-align: 1px; white-space: nowrap; }
.zm-play { display: inline-flex; align-items: center; gap: 6px; margin-top: 8px; padding: 5px 12px 5px 9px; border-radius: 999px;
    border: 1px solid #e3dcd2; background: #f8f5f0; color: #5e4532; font-size: 12px; font-weight: 550; cursor: pointer; }
.zm-play:hover { background: #eee6db; }
.zm-play .zm-icon { width: 16px; height: 16px; }
.zm-play.playing { background: #211e1b; color: #fbf8f3; border-color: #211e1b; }
.zm-play.playing .ih-wave1, .zm-play.playing .ih-wave2 { animation: ih-wave 1s ease-in-out infinite; }
.zm-play.playing .ih-wave2 { animation-delay: .2s; }
.typing { display: inline-flex; gap: 4px; padding: 4px 0; }
.typing i { width: 7px; height: 7px; border-radius: 50%; background: #b8a896; animation: zm-bounce 1.2s infinite ease-in-out; }
.typing i:nth-child(2) { animation-delay: .15s; } .typing i:nth-child(3) { animation-delay: .3s; }
@keyframes zm-bounce { 0%, 60%, 100% { transform: translateY(0); opacity: .5; } 30% { transform: translateY(-4px); opacity: 1; } }
.conversation-empty { text-align: center; color: #8c7762; }
.empty-mark { display: inline-grid; place-items: center; width: 52px; height: 52px; border-radius: 16px; background: #fff;
    border: 1px solid #e3dcd2; color: #a3825f; margin-bottom: 14px; }
.empty-mark .zm-icon { width: 26px; height: 26px; }
.empty-title { font-size: 24px; font-weight: 500; letter-spacing: -.7px; color: #3b2f25; margin-bottom: 8px; }
.empty-description { max-width: 340px; margin: 0 auto; color: #817264; font-size: 14px; line-height: 1.7; }

/* Composer */
#composer-wrap { position: sticky; bottom: 0; z-index: 5; background: linear-gradient(to bottom, rgba(244,240,233,0), #f4f0e9 18px);
    padding-top: 14px !important; }
#zm-composer { background: #ffffff; border: 1px solid #ddd5ca; border-radius: 28px; padding: 6px;
    box-shadow: 0 2px 10px rgba(33,30,27,.06); transition: border-color 150ms ease; }
#zm-composer:focus-within { border-color: #b9ab9b; }
.zm-type, .zm-rec { display: flex; align-items: flex-end; gap: 4px; }
.zm-rec { display: none; align-items: center; }
#zm-composer.recording .zm-type { display: none; }
#zm-composer.recording .zm-rec { display: flex; }
#zm-input { flex: 1; min-width: 0; resize: none; border: 0; outline: none !important; background: transparent; color: #211e1b;
    font-size: 15px; line-height: 22px; padding: 9px 6px; max-height: 160px; }
#zm-input { overflow-y: hidden; }
#zm-input::placeholder { color: #8a7d70; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.zm-btn { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50% !important; border: 0; cursor: pointer;
    padding: 0 !important; flex: none; transition: background-color 150ms ease, transform 150ms ease; }
.zm-btn.ghost { background: transparent; color: #6c5440; }
.zm-btn.ghost:hover { background: #f1ebe2; }
.zm-btn.primary { background: #211e1b; color: #fbf8f3; }
.zm-btn.primary:hover { background: #674c38; }
.zm-btn:active { transform: scale(.94); }
#zm-send { display: none; }
#zm-composer.has-text #zm-send { display: grid; }
#zm-composer.has-text #zm-mic { display: none; }
#zm-composer.busy .zm-btn.primary { opacity: .45; pointer-events: none; }
.zm-dot { width: 10px; height: 10px; border-radius: 50%; background: #c2412d; margin-left: 4px; animation: zm-pulse 1.2s infinite; }
@keyframes zm-pulse { 50% { opacity: .35; } }
#zm-timer { font-variant-numeric: tabular-nums; font-size: 14px; color: #3b2f25; min-width: 36px; }
#zm-wave { flex: 1; min-width: 0; height: 30px; display: flex; align-items: center; justify-content: flex-end; gap: 2px; overflow: hidden; }
#zm-wave i { width: 3px; border-radius: 2px; background: #7b5d47; flex: none; }
#zm-hint { font-size: 12px; color: #8a7d70; white-space: nowrap; padding-right: 6px; }
#zm-note { margin: 8px 0 0; text-align: center; font-size: 11px; color: #9a8c7e; }
#session-status { padding: 2px 0 0; background: transparent; text-align: center; }
#session-status p { font-size: 12px; color: #817264; margin: 0; }
#bridge { display: none !important; }

/* Its Hover animations, recreated in CSS */
.ih-plane, .ih-arrow, .ih-spin, .ih-x, .ih-items, .ih-spark, .ih-spark-s { transition: transform 300ms ease, opacity 300ms ease;
    transform-box: fill-box; transform-origin: center; }
#zm-send:hover .ih-plane, #zm-stop:hover .ih-plane { transform: translateX(2px); opacity: .8; }
#zm-upload:hover .ih-arrow { transform: translateY(-2px); }
#reset::before { content: ''; width: 14px; height: 14px; background: currentColor; transition: transform 300ms ease;
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4'/%3E%3Cpath d='M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4'/%3E%3C/svg%3E") center / contain no-repeat;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4'/%3E%3Cpath d='M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4'/%3E%3C/svg%3E") center / contain no-repeat; }
#reset:hover::before { transform: rotate(180deg); }
#zm-cancel:hover .ih-x { transform: rotate(90deg); }
.zm-logo:hover .ih-items { animation: ih-bounce .5s ease; }
.zm-sub:hover .ih-spark, .empty-mark:hover .ih-spark { transform: scale(1.15) rotate(10deg); }
.zm-play:hover .ih-wave1, .zm-play:hover .ih-wave2 { animation: ih-wave 1s ease-in-out infinite; }
@keyframes ih-wave { 50% { opacity: .3; } }
@keyframes ih-bounce { 40% { transform: translateY(-3px); } }

/* Behind the scenes */
#details { margin-top: 22px; border-top: 1px solid #dcd4c9 !important; padding-top: 14px !important; background: transparent !important; }
#details > button { padding: 0 !important; font-size: 14px; font-weight: 600; color: #3b2f25; }
#details > div { padding: 12px 0 0 !important; }
#ins-toolbar { align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 4px; }
#ins-toolbar > div { flex: 1 1 320px; min-width: 0; }
.ins-intro { margin: 0; font-size: 12.5px; line-height: 1.6; color: #817264; }
#inspect { flex: 0 0 auto; width: auto !important; min-width: 0 !important; border-radius: 999px !important; padding: 7px 14px !important;
    background: #ffffff !important; color: #5e4532 !important; border: 1px solid #ddd5ca !important; font-size: 12px !important; }
#inspect:hover { background: #f1ebe2 !important; }
#inspector, #inspector .prose { background: transparent !important; }
.ins-empty { padding: 26px 20px; border: 1px dashed #d8cec2; border-radius: 14px; text-align: center; font-size: 13px; line-height: 1.6; color: #8a7d70; }
.ins { display: flex; flex-direction: column; gap: 14px; }
.ins-head { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.ins-kicker { font-size: 11px; font-weight: 650; letter-spacing: .08em; text-transform: uppercase; color: #a3825f; }
.ins-status { font-size: 12px; color: #817264; }
.ins-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(118px, 1fr)); gap: 8px; }
.ins-stat { background: #ffffff; border: 1px solid #e7e0d6; border-radius: 12px; padding: 10px 12px; }
.ins-stat span { display: block; font-size: 11px; color: #8a7d70; margin-bottom: 3px; }
.ins-stat b { font-size: 17px; font-weight: 600; color: #211e1b; letter-spacing: -.3px; font-variant-numeric: tabular-nums; }
.ins-stat.ok b { color: #2f6b45; }
.ins section { background: #ffffff; border: 1px solid #e7e0d6; border-radius: 14px; padding: 14px 16px; }
.ins h4 { margin: 0 0 10px !important; font-size: 13px !important; font-weight: 650 !important; color: #3b2f25 !important; }
.ins h4 small { font-weight: 400; color: #9a8c7e; font-size: 12px; margin-left: 6px; }
.ins-heard { margin: 0 !important; font-size: 15px; line-height: 1.6; color: #211e1b; }
.ins-rewrite { margin: 8px 0 0 !important; font-size: 12.5px; color: #6c5440; }
.ins-rewrite span { display: inline-block; margin-right: 8px; padding: 1px 8px; border-radius: 999px; background: #f1ebe2; font-size: 11px; font-weight: 600; }
.ins-none { margin: 0 !important; color: #9a8c7e; font-size: 13px; }
.ins-cards { display: flex; flex-direction: column; gap: 6px; }
.ins-card { border: 1px solid #ece5db; border-radius: 10px; background: #fcfaf7; overflow: hidden; }
.ins-card.cited { border-color: #c9b39a; background: #fbf6ef; box-shadow: inset 3px 0 0 #a3825f; }
.ins-card summary { display: grid; grid-template-columns: auto 1fr auto; grid-template-areas: "sid title score" "flags flags flags";
    align-items: center; gap: 4px 10px; padding: 9px 12px; cursor: pointer; list-style: none; }
.ins-card summary::-webkit-details-marker { display: none; }
.ins-card summary:hover { background: #f6f1ea; }
.ins-sid { grid-area: sid; font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; font-weight: 600; color: #5e4532; }
.ins-title { grid-area: title; min-width: 0; font-size: 13px; color: #211e1b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ins-flags { grid-area: flags; display: flex; flex-wrap: wrap; gap: 4px; }
.ins-type, .ins-flag { display: inline-block; padding: 0 7px; border-radius: 999px; font-size: 10.5px; font-weight: 600; line-height: 18px; }
.ins-type { background: #eee6db; color: #6c5440; }
.ins-type.policy { background: #e6eee5; color: #2f5b3a; }
.ins-type.guide { background: #e7ebf3; color: #36507a; }
.ins-type.faq, .ins-type.help { background: #f3ece1; color: #7a5d45; }
.ins-type.mkt { background: #f5e6e3; color: #8a3f33; }
.ins-type.catalog { background: #ece7f3; color: #5a4380; }
.ins-flag.ok { background: #211e1b; color: #fbf8f3; }
.ins-flag.warn { background: #fbe6d4; color: #8a4b16; }
.ins-score { grid-area: score; width: 70px; height: 5px; border-radius: 3px; background: #ece5db; overflow: hidden; }
.ins-score i { display: block; height: 100%; background: #a3825f; border-radius: 3px; }
.ins-meta { padding: 0 12px; font-size: 11px; color: #9a8c7e; }
.ins-text { padding: 6px 12px 12px; font-size: 13px; line-height: 1.6; color: #45392e; white-space: pre-wrap; }
.ins-steps { list-style: none; margin: 0 !important; padding: 0 !important; display: flex; flex-direction: column; }
.ins-step { position: relative; display: grid; grid-template-columns: 14px 1fr; gap: 10px; padding: 0 0 12px; margin: 0 !important; }
.ins-step:not(:last-child)::after { content: ''; position: absolute; left: 6px; top: 16px; bottom: 0; width: 2px; background: #ece5db; }
.ins-dot { width: 14px; height: 14px; border-radius: 50%; background: #ffffff; border: 2px solid #b8a896; margin-top: 2px; z-index: 1; }
.ins-step.ok .ins-dot { border-color: #2f6b45; background: #e6eee5; }
.ins-step.bad .ins-dot { border-color: #b4462f; background: #f8e3dd; }
.ins-step b { font-size: 13px; color: #211e1b; }
.ins-step code { margin-left: 6px; font-size: 11px; color: #9a8c7e; background: none; padding: 0; }
.ins-args { margin: 2px 0 0 !important; font-size: 12px; color: #817264; word-break: break-word; }
.ins-res { margin: 2px 0 0 !important; font-size: 12.5px; color: #3b2f25; word-break: break-word; }
.ins-step.ok .ins-res { color: #2f5b3a; } .ins-step.bad .ins-res { color: #9a3a26; }
.ins-session { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; }
.ins-session div { background: #fcfaf7; border: 1px solid #ece5db; border-radius: 10px; padding: 8px 10px; min-width: 0; }
.ins-session span { display: block; font-size: 11px; color: #8a7d70; }
.ins-session b { font-size: 13px; font-weight: 600; color: #211e1b; word-break: break-all; }
.ins-raw summary { cursor: pointer; font-size: 12px; color: #817264; }
.ins-raw pre { max-height: 320px; overflow: auto; margin: 8px 0 0; padding: 12px; border-radius: 10px; background: #ffffff;
    border: 1px solid #e7e0d6; font-size: 11px; line-height: 1.5; color: #5e4532; }
#app-footer { background: transparent; padding: 18px 0 0; }
#app-footer p { font-size: 11px; color: #75695d; margin: 0; text-align: center; }
@media (max-width: 640px) {
    .gradio-container { padding: 0 12px 18px !important; }
    #conversation .message { max-width: 90%; }
    .zm-sub { display: none; }
    #zm-hint { display: none; }
}
@media (prefers-reduced-motion: reduce) {
    .gradio-container *, .gradio-container *::before, .gradio-container *::after { transition: none !important; animation: none !important; }
}
"""


EMPTY_CONVERSATION = f"""
<div class="conversation-empty">
    <div class="empty-mark">{ICONS['sparkles']}</div>
    <div class="empty-title">How can we help?</div>
    <p class="empty-description">Ask about an order, a return or a refund.<br>Type below, or tap the mic and speak.</p>
</div>
"""
