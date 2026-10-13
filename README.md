# TransNova — Multilingual LLM Translation Platform

**Customized by Sandeep Patra** · Python · Streamlit · Pydantic · n8n · Google Gemini

TransNova provides a responsive UI for translating text through an operator-configured n8n workflow. This customized version adds schema validation, robust webhook response parsing, a timeout/error boundary, safe plain-text rendering, a session history, downloadable text/JSON output, an optional domain/terminology hint, and a neutral workflow template that does not use someone else's live webhook.

## Features

- Language selector with more than 30 destination options, including Indian languages such as Odia, Hindi, Bengali, Tamil and Telugu.
- Pydantic request/response contracts: blank input, excessive input, and malformed output are rejected before being shown as a successful result.
- Supports common n8n response shapes (`[{"output": "..."}]`, `{"output": "..."}`, `{"translation": "..."}`, or a plain string).
- Configurable source-language preference and a domain/terminology note passed to the workflow.
- Explicit connection timeout, HTTP error handling, output as plain text instead of injected HTML, per-session recent history, and text/JSON downloads.

The app itself does not run an LLM locally: translation requires your own n8n workflow and Gemini credential. Streaming tokens and measured latency claims are not implemented in this version.

## Architecture

- `app.py`: Streamlit interface and status/error handling.
- `transnova_core.py`: Pydantic contracts, normalized response parser, and webhook client.
- `tests/test_core.py`: unit tests for contracts and response parsing.
- `Lang_Translatn_Streamlit_Application using Webhook.json`: workflow export template for n8n. It has a new webhook path and no inherited webhook ID or Google credential binding; you must configure your own credential in n8n.
- `.env.example`: placeholder for your own webhook endpoint.

## Setup

1. Install Python 3.10 or later.
2. Create and activate a virtual environment, then run:
   ```bash
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. In n8n, import the workflow JSON, connect your own Google Gemini credential, verify the AI Agent's input fields, save, activate the workflow, and copy its **production** webhook URL.
4. Set the URL in the same terminal before starting Streamlit:
   ```bash
   # Windows PowerShell
   $env:N8N_WEBHOOK_URL="https://YOUR-N8N-HOST/webhook/transnova-translate"
   streamlit run app.py
   ```
   Or place `N8N_WEBHOOK_URL` in `.streamlit/secrets.toml` (do not commit that file). See `.env.example` for the placeholder format; Streamlit does not automatically load `.env` in every configuration, so set the environment variable explicitly or use its secrets mechanism.
5. Open `http://localhost:8501`.

## Request contract

The UI posts a JSON object like:

```json
{
  "text": "The system-on-chip passed validation.",
  "target_language": "or",
  "language_name": "Odia (ଓଡ଼ିଆ)",
  "source_language": "Auto-detect",
  "context": "Semiconductor engineering; preserve product names."
}
```

The included n8n agent prompt reads those fields and should return its translation under `output`. Confirm the imported workflow output in a test execution before using it for real documents.

## Automated tests

```bash
python -m unittest discover -s tests -v
```

These tests validate the input contract and common n8n response shapes without needing a live webhook.

## Testing checklist

- Try English → Odia and English → Hindi with short and multi-paragraph text.
- Check line breaks, numbers, URLs and product terms.
- Test the missing-webhook message, stopped workflow, invalid JSON and empty output.
- Do not send private or confidential documents to an external model unless you have permission to do so.

## About the developer

Sandeep Patra has a B.Tech background in Electronics and Telecommunication Engineering from Parala Maharaja Engineering College, interested in full-stack engineering and AI-driven applications.

## Upstream acknowledgement

This working copy was adapted from the supplied public project **[ChallaRake/Language-Translation-App-Streamlit-n8n-Gemini-](https://github.com/ChallaRake/Language-Translation-App-Streamlit-n8n-Gemini-)**. The supplied archive did not include a project-level `LICENSE` file. This version removes the hard-coded third-party webhook endpoint, resets the workflow webhook path, removes the inherited webhook ID and credential binding, and adds the validation/configuration changes above. Check the upstream repository's current license/permission before publishing a derivative repository.
