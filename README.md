# PromptForge Aggregator - Free Student Edition

A Streamlit app that optimizes prompts for coding agents and AI research using multiple Groq-powered optimizers. Paste once → get 4 variants → smart winner + fusion.

## Features
- 4 optimizers: Coding (structured/JSON), Research (hypothesis/metrics), Concise (token-saver), Structured (role/task/steps).
- AI judge picks winner + fuses best parts.
- Free Groq API (supports Llama 3.1/3.3 models).
- Dark theme, progress indicators, token estimates.
- Secure secrets management (no exposed API keys).

## Setup Locally
1. Clone repo: `git clone https://github.com/ssam-dev/prompt-forge.git`
2. Install deps: `pip install -r requirements.txt`
3. Add Groq key: Create `.streamlit/secrets.toml` with `GROQ_API_KEY = "your_groq_key_here"` (get free key at console.groq.com).
4. Run: `streamlit run app.py`

## Deployment (Recommended: Streamlit Cloud)
1. Push to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → Select repo → Set `app.py`.
3. Add secret: `GROQ_API_KEY = your_key_here`.
4. Deploy!

## Security Notes
- API key is server-side only (via secrets.toml or env vars).
- Never commit keys — .gitignore ignores .env/secrets.toml.

## Known Issues
- Groq rate limits: Use 8B model for heavy use; retry logic handles most.
- Contributions welcome!

Built by Samarth in Pune, 2026.
