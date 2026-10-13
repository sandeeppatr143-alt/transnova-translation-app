"""TransNova: a validated, multilingual translation interface.

The UI talks to an n8n webhook configured by the operator. It never embeds a
third-party user's live webhook URL in source code.
"""
from __future__ import annotations

import os
import requests
import streamlit as st
from pydantic import ValidationError

from transnova_core import TranslationRequest, TranslationResponse, request_translation


LANGUAGES: dict[str, str] = {
    "Arabic (العربية)": "ar", "Bengali (বাংলা)": "bn", "Chinese (Simplified)": "zh-CN",
    "Dutch": "nl", "English": "en", "French": "fr", "German": "de", "Gujarati (ગુજરાતી)": "gu",
    "Hindi (हिन्दी)": "hi", "Indonesian": "id", "Italian": "it", "Japanese": "ja", "Kannada (ಕನ್ನಡ)": "kn",
    "Korean": "ko", "Malayalam (മലയാളം)": "ml", "Marathi (मराठी)": "mr", "Nepali": "ne",
    "Odia (ଓଡ଼ିଆ)": "or", "Persian": "fa", "Polish": "pl", "Portuguese": "pt", "Punjabi (ਪੰਜਾਬੀ)": "pa",
    "Russian": "ru", "Sanskrit (संस्कृतम्)": "sa", "Spanish": "es", "Swahili": "sw", "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te", "Thai": "th", "Turkish": "tr", "Ukrainian": "uk", "Urdu (اردو)": "ur",
    "Vietnamese": "vi",
}



def configured_webhook_url() -> str:
    """Read the endpoint from environment or Streamlit secrets."""
    value = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not value:
        try:
            value = str(st.secrets.get("N8N_WEBHOOK_URL", "")).strip()
        except Exception:
            value = ""
    return value


st.set_page_config(page_title="TransNova | Sandeep Patra", page_icon="🌐", layout="wide")
st.markdown("""
<style>
:root { --ink: #162239; --muted: #63718a; --accent: #5b5be9; --mint: #dff8f0; }
.block-container { max-width: 1100px; padding-top: 2rem; padding-bottom: 3rem; }
.transnova-hero { padding: 2rem 2.2rem; border-radius: 22px; background: linear-gradient(125deg,#17243c,#333a78 62%,#4c69a8); color: white; margin-bottom: 1.5rem; }
.transnova-hero h1 { color: white; letter-spacing: -.04em; font-size: clamp(2rem,4.5vw,3.3rem); margin: .5rem 0; }
.transnova-hero p { color: #e0e7ff; max-width: 720px; margin-bottom: 0; }
.eyebrow { text-transform: uppercase; letter-spacing: .18em; font-size: .72rem; font-weight: 700; color: #c4d2ff; }
.stButton > button[kind="primary"] { background: var(--accent); border-color: var(--accent); }
</style>
<div class="transnova-hero">
  <div class="eyebrow">Multilingual writing utility</div>
  <h1>TransNova</h1>
  <p>Translate longer passages with formatting, terminology, and meaning in mind. Built with Streamlit, Pydantic contracts, and an n8n + Gemini workflow.</p>
</div>
""", unsafe_allow_html=True)

webhook_url = configured_webhook_url()
if not webhook_url:
    st.warning("Translation backend is not configured yet. Set `N8N_WEBHOOK_URL` in your environment or Streamlit secrets after importing and activating your own n8n workflow.")

left, right = st.columns([1.65, 1], gap="large")
with left:
    st.subheader("Source text")
    with st.form("translation-form", clear_on_submit=False):
        source_language = st.selectbox("Source language", ["Auto-detect", *LANGUAGES.keys()], index=0)
        source_text = st.text_area("Text to translate", height=250, max_chars=20_000, placeholder="Paste a paragraph, email, or document excerpt here…")
        context = st.text_input("Domain or terminology notes (optional)", max_chars=500, placeholder="e.g. semiconductor engineering, keep product names unchanged")
        target_language = st.selectbox("Translate into", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index("Odia (ଓଡ଼ିଆ)"))
        submitted = st.form_submit_button("Translate text", type="primary", use_container_width=True)
with right:
    st.subheader("Translation setup")
    st.markdown("**Supported destinations**")
    st.write(f"{len(LANGUAGES)} language options")
    st.markdown("**Input safeguards**")
    st.write("Up to 20,000 characters per request")
    st.write("Validated request and normalized response schema")
    st.write("Webhook timeout and HTTP error handling")
    st.caption("Translation quality depends on the configured model and workflow instructions.")

if submitted:
    try:
        request_data = TranslationRequest(
            text=source_text,
            target_language=LANGUAGES[target_language],
            language_name=target_language,
            source_language=source_language,
            context=context.strip(),
        )
    except ValidationError as exc:
        first_error = exc.errors()[0]
        st.error(first_error.get("msg", "Please check the source text."))
    else:
        if not webhook_url:
            st.error("Add your own `N8N_WEBHOOK_URL` before requesting a translation.")
        else:
            with st.spinner("Translating with your configured workflow…"):
                try:
                    result = request_translation(request_data, webhook_url)
                except requests.Timeout:
                    st.error("The workflow timed out. Check that n8n is active and try again.")
                except requests.HTTPError as exc:
                    status = exc.response.status_code if exc.response is not None else "unknown"
                    st.error(f"The translation workflow returned HTTP {status}. Check the n8n execution log.")
                except requests.RequestException as exc:
                    st.error(f"Could not reach the translation workflow: {exc}")
                except (ValueError, ValidationError) as exc:
                    st.error(f"Could not validate the translation result: {exc}")
                else:
                    st.session_state["transnova_latest"] = result.model_dump()
                    history = st.session_state.setdefault("transnova_history", [])
                    history.insert(0, {**result.model_dump(), "source_text": request_data.text, "context": request_data.context})
                    st.session_state["transnova_history"] = history[:10]

latest = st.session_state.get("transnova_latest")
if latest:
    st.divider()
    st.subheader(f"Result · {latest['target_language']}")
    st.text_area("Translated text", value=latest["translation"], height=260, key=f"latest_translation_view_{latest['created_at']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Output characters", f"{latest['character_count']:,}")
    c2.metric("Target language", latest["target_language"])
    c3.caption(f"Created {latest['created_at']}")
    st.download_button("Download .txt", data=latest["translation"], file_name="transnova_translation.txt", mime="text/plain")
    st.download_button("Download validated JSON", data=__import__("json").dumps(latest, ensure_ascii=False, indent=2), file_name="transnova_result.json", mime="application/json")

with st.expander("Recent translations in this session"):
    history = st.session_state.get("transnova_history", [])
    if not history:
        st.caption("Translations from this session will appear here. History stays in Streamlit session state.")
    else:
        for idx, item in enumerate(history):
            with st.container(border=True):
                st.markdown(f"**{item['target_language']}** · {item['character_count']:,} output characters")
                st.caption(item["created_at"])
                st.text(item["source_text"][:240] + ("…" if len(item["source_text"]) > 240 else ""))
                st.download_button("Download this result", data=item["translation"], file_name=f"transnova_translation_{idx + 1}.txt", mime="text/plain", key=f"history-download-{idx}")

st.divider()
st.markdown("<div style='display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;color:#718096;font-size:.85rem'><span>Built and customized by <b>Sandeep Patra</b></span><span>Python · Streamlit · Pydantic · n8n · Gemini</span></div>", unsafe_allow_html=True)
