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


CSS = """
:root, body, .dark { color-scheme: light; background: #f4f0e9 !important; }
body { margin: 0; -webkit-font-smoothing: antialiased; }
.gradio-container {
    width: 100% !important; max-width: 1240px !important;
    margin: 0 auto !important; padding: 0 36px 24px !important;
    font-family: 'Helvetica Neue', Arial, sans-serif !important;
    color: #211e1b !important; background: #f4f0e9 !important;
}
.gradio-container footer { display: none !important; }
.gradio-container .form { border: 0 !important; box-shadow: none !important; background: transparent !important; }
.gradio-container button, .gradio-container textarea { font-family: inherit !important; }
.gradio-container button { box-shadow: none !important; }
.gradio-container button:focus-visible, .gradio-container textarea:focus-visible {
    outline: 2px solid #7b5d47 !important; outline-offset: 3px !important;
}
.gradio-container button:active { transform: translateY(1px); }
.gradio-container textarea { font-size: 14px !important; line-height: 1.55 !important; }
.gradio-container label > span { background: transparent !important; }
#topbar { background: transparent; border-bottom: 1px solid #dcd4c9; padding: 22px 0 18px; }
.brandbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.brand { font-size: 23px; font-weight: 650; letter-spacing: -1px; line-height: 1; }
.brand-detail { color: #726253; font-size: 12px; letter-spacing: .01em; }
#intro { background: transparent; padding: 22px 0 18px; }
#intro h1 { font-size: clamp(30px, 3.2vw, 42px); font-weight: 500; line-height: 1.12; letter-spacing: -1.6px; margin: 0 0 12px; }
#intro p { color: #756b62; font-size: 14px; line-height: 1.6; margin: 0; }
#workspace {
    gap: 0 !important; background: #ffffff; border: 1px solid #ddd5ca;
    border-radius: 12px; overflow: hidden; align-items: stretch;
}
#conversation-panel { padding: 24px 28px 20px; min-width: 0 !important; gap: 16px; }
#session-panel { padding: 25px 24px 24px; min-width: 0 !important; border-left: 1px solid #e7e0d7; gap: 16px; }
#conversation-heading { align-items: center; flex-wrap: nowrap; gap: 12px; }
.panel-title { margin: 0; font-size: 16px; font-weight: 550; letter-spacing: -.35px; line-height: 1.5; }
#reset { flex: 0 0 auto; min-width: 0 !important; width: auto !important; padding: 7px 11px; font-size: 11px; height: 32px; }
#conversation { background: #ffffff !important; border: 0 !important; padding: 0 !important; border-radius: 0 !important; }
#conversation .bubble-wrap { padding: 0 !important; }
#conversation .placeholder-content { padding: 20px; }
.conversation-empty { text-align: center; color: #8c7762; }
.empty-title { font-size: 23px; font-weight: 450; letter-spacing: -.7px; color: #6c5440; margin-bottom: 10px; }
.empty-description { max-width: 270px; margin: 0 auto; color: #817264; font-size: 13px; line-height: 1.7; }
#conversation .message { font-size: 14px !important; line-height: 1.65 !important; border-radius: 8px !important; box-shadow: none !important; }
#conversation .user { background: #eee6db !important; color: #352a21 !important; }
#conversation .bot { background: #f8f5f0 !important; color: #211e1b !important; }
#composer { gap: 12px; align-items: end; flex-wrap: nowrap; }
#message-input { min-width: 0 !important; }
#message-input textarea { background: #f8f5f0 !important; min-height: 72px; padding: 12px 14px !important; }
#send { flex: 0 0 146px; min-width: 146px !important; height: 72px; padding: 12px; }
#voice-input { border-top: 1px solid #e7e0d7; padding-top: 15px; background: transparent !important; }
#voice-input > button { padding: 0 !important; font-size: 12px; font-weight: 500; }
#voice-input > div { padding: 16px 0 0 !important; }
#microphone { border: 1px solid #e3dcd2 !important; border-radius: 6px !important; padding: 10px !important; background: #f8f5f0 !important; }
#microphone .record-button { color: #674c38 !important; }
#transcript textarea, #session-status textarea { padding: 11px 12px !important; background: #f8f5f0 !important; border-color: transparent !important; }
#session-status textarea { color: #6c5440 !important; font-size: 12px !important; }
#reply-audio { min-height: 90px; }
#reply-audio audio { width: 100%; }
.detail-disclosure { border-top: 1px solid #e7e0d7 !important; padding-top: 15px !important; background: transparent !important; }
.detail-disclosure > button { padding: 0 !important; font-size: 12px; font-weight: 500; }
.detail-disclosure > div { padding: 16px 0 0 !important; }
#evidence, #tool-calls { max-height: 320px !important; overflow: auto; background: #f8f5f0 !important; border-radius: 6px; }
#evidence *, #tool-calls * { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 11px; color: #71563f !important; }
#evidence .json-node, #tool-calls .json-node { background: transparent !important; }
#evidence .key, #tool-calls .key { color: #352a21 !important; font-weight: 500; }
#evidence .punctuation, #tool-calls .punctuation { color: #817264 !important; }
#inspect { background: #eee6db !important; color: #5e4532 !important; border-color: #eee6db !important; min-height: 40px; font-size: 12px; }
#inspect:hover { background: #e5d8c8 !important; }
#inspect-note { margin-top: -13px; background: transparent; }
#inspect-note p { font-size: 11px; line-height: 1.6; color: #817264; margin: 0; }
#app-footer { background: transparent; padding: 17px 0 0; }
#app-footer p { font-size: 11px; color: #75695d; margin: 0; }
@media (max-width: 760px) {
    .gradio-container { padding: 0 18px 22px !important; }
    #topbar { padding: 22px 0 20px; }
    .brand { font-size: 21px; }
    .brand-detail { font-size: 11px; }
    #intro { padding: 25px 0 21px; }
    #intro h1 { letter-spacing: -1px; }
    #workspace { flex-direction: column !important; }
    #conversation-panel { padding: 20px 18px; }
    #session-panel { border-left: 0; border-top: 1px solid #e7e0d7; padding: 22px 18px; }
    #conversation { height: 245px !important; }
    #composer { gap: 8px; }
    #send { flex-basis: 116px; min-width: 116px !important; font-size: 12px; }
    .conversation-empty { max-width: 250px; }
}
@media (prefers-reduced-motion: reduce) {
    .gradio-container *, .gradio-container *::before, .gradio-container *::after { transition: none !important; animation: none !important; }
}
"""


EMPTY_CONVERSATION = """
<div class="conversation-empty">
    <div class="empty-title">Here to help.</div>
    <p class="empty-description">Ask about an order, a return or a refund.<br>Your conversation starts here.</p>
</div>
"""
