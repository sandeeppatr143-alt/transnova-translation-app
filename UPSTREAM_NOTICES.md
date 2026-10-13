# Upstream code and changes

Adapted from the supplied archive for **ChallaRake/Language-Translation-App-Streamlit-n8n-Gemini-**: https://github.com/ChallaRake/Language-Translation-App-Streamlit-n8n-Gemini-.

Main changes: replaced the original UI and hard-coded external webhook, added Pydantic request/result models, response normalization, error/timeout handling, safe text display, domain context, session history, downloads, and updated the n8n workflow template to remove the old webhook ID and credential reference.

The supplied archive contained no project-level `LICENSE` file. Verify the upstream license and obtain permission as needed before redistribution. The n8n workflow also requires the user to configure their own Gemini credential and webhook URL.
