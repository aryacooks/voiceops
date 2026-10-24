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
    width: 100% !important; max-width: 860px !important;
    margin: 0 auto !important; padding: 0 20px 24px !important;
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
.gradio-container label > span { background: transparent !important; }

/* Header */
#topbar { align-items: center; justify-content: space-between; flex-wrap: nowrap; gap: 12px;
    padding: 18px 0 14px; border-bottom: 1px solid #dcd4c9; background: transparent; }
.brand { font-size: 21px; font-weight: 650; letter-spacing: -.8px; line-height: 1.2; }
.brand-detail { display: block; color: #726253; font-size: 12px; font-weight: 400; letter-spacing: .01em; margin-top: 2px; }
#reset { flex: 0 0 auto; width: auto !important; min-width: 0 !important; padding: 7px 12px; font-size: 12px; }

/* Conversation */
#conversation { background: transparent !important; border: 0 !important; padding: 8px 0 0 !important; }
#conversation .bubble-wrap { padding: 8px 0 !important; background: transparent !important; }
#conversation .placeholder-content { padding: 20px; }
#conversation .message { font-size: 15px !important; line-height: 1.6 !important; border-radius: 16px !important;
    box-shadow: none !important; padding: 10px 14px !important; max-width: 82%; }
#conversation .user { background: #211e1b !important; color: #fbf8f3 !important; border: 0 !important;
    border-bottom-right-radius: 4px !important; }
#conversation .bot { background: #ffffff !important; color: #211e1b !important; border: 1px solid #e3dcd2 !important;
    border-bottom-left-radius: 4px !important; }
#conversation .user * { color: #fbf8f3 !important; }
#conversation .top-panel, #conversation .icon-button-wrapper.top-panel { display: none !important; }
.typing { color: #8c7762; font-style: italic; white-space: nowrap;animation: typing 1.4s ease-in-out infinite; }
@keyframes typing { 50% { opacity: .45; } }
#conversation .bot audio { width: 260px; max-width: 100%; height: 36px; }
#conversation .avatar-container { display: none !important; }
.cite { display: inline-block; margin: 0 2px; padding: 0 6px; border-radius: 999px; background: #eee6db;
    color: #6c5440; font-size: 11px; font-weight: 500; line-height: 18px; vertical-align: 1px; }
.conversation-empty { text-align: center; color: #8c7762; }
.empty-title { font-size: 26px; font-weight: 450; letter-spacing: -.8px; color: #6c5440; margin-bottom: 10px; }
.empty-description { max-width: 320px; margin: 0 auto; color: #817264; font-size: 14px; line-height: 1.7; }

/* Composer: one pill with attach, mic and send */
#composer { background: #ffffff !important; border: 1px solid #ddd5ca !important; border-radius: 26px !important;
    padding: 6px 8px 6px 10px !important; box-shadow: 0 1px 2px rgba(33,30,27,.04) !important; }
#composer textarea { background: transparent !important; border: 0 !important; font-size: 15px !important;
    padding: 10px 6px !important; }
#composer button { border-radius: 999px !important; }
#composer .submit-button { background: #211e1b !important; color: #fff !important; }
#composer .submit-button:hover { background: #674c38 !important; }
#composer .microphone-button, #composer .upload-button { color: #674c38 !important; }
#composer .record-button, #composer .stop-button { color: #674c38 !important; }
#session-status { padding: 6px 16px 0; background: transparent; }
#session-status p { font-size: 12px; color: #817264; margin: 0; }
#autoplay { position: absolute !important; width: 1px !important; height: 1px !important; overflow: hidden !important;
    opacity: 0 !important; pointer-events: none !important; }

/* Behind the scenes */
#details { margin-top: 18px; border-top: 1px solid #dcd4c9 !important; padding-top: 14px !important; background: transparent !important; }
#details > button { padding: 0 !important; font-size: 13px; font-weight: 550; color: #45392e; }
#details > div { padding: 14px 0 0 !important; }
.details-note p { font-size: 12px; line-height: 1.6; color: #817264; margin: 0 0 4px; }
#transcript textarea { padding: 11px 12px !important; background: #ffffff !important; border-color: #e3dcd2 !important; }
#evidence, #tool-calls { overflow: auto; background: #ffffff !important; border: 1px solid #e3dcd2 !important; border-radius: 8px; }
#evidence *, #tool-calls * { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 11px; color: #71563f !important; }
#evidence .json-node, #tool-calls .json-node { background: transparent !important; }
#evidence .key, #tool-calls .key { color: #352a21 !important; font-weight: 500; }
#inspect { background: #eee6db !important; color: #5e4532 !important; border-color: #eee6db !important; min-height: 38px; font-size: 12px; }
#inspect:hover { background: #e5d8c8 !important; }
#app-footer { background: transparent; padding: 18px 0 0; }
#app-footer p { font-size: 11px; color: #75695d; margin: 0; }
@media (max-width: 640px) {
    .gradio-container { padding: 0 14px 20px !important; }
    #conversation .message { max-width: 92%; }
}
@media (prefers-reduced-motion: reduce) {
    .gradio-container *, .gradio-container *::before, .gradio-container *::after { transition: none !important; animation: none !important; }
}
"""


EMPTY_CONVERSATION = """
<div class="conversation-empty">
    <div class="empty-title">Here to help.</div>
    <p class="empty-description">Ask about an order, a return or a refund.<br>Type below, or tap the mic and speak.</p>
</div>
"""
