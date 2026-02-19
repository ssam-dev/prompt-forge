import asyncio
from typing import Dict

import streamlit as st
import litellm
from backend import run_optimizers, get_winner_and_scores, get_fusion, estimate_tokens
from litellm import completion

st.set_page_config(
    page_title="PromptForge Aggregator - Free Student Edition",
    page_icon="🛠️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stSidebar { background-color: #161b22; border-right: 1px solid #30363d; }
    h1 { color: #58a6ff; text-align: center; font-size: 2.6rem; margin-bottom: 0.4rem; }
    .subtitle { color: #8b949e; text-align: center; font-size: 1.05rem; margin-top: 0; }
    button[kind="primary"] { background-color: #238636; color: white; border-radius: 8px; padding: 0.6rem 1.2rem; }
    button[kind="primary"]:hover { background-color: #2ea043; }
    .stTextArea textarea { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 8px; }
    .stExpander { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_api_key() -> str:
    """Get API key from Streamlit secrets only. Returns empty string if not found."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, AttributeError):
        return ""

def groq_health_check(model: str, api_key: str) -> Dict[str, str]:
    """Optional litellm Groq ping to verify key/model wiring. Not required for placeholders."""
    try:
        if not api_key:
            return {"status": "skipped", "message": "No API key provided."}

        response = completion(
            model=model,
            api_key=api_key,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: PromptForge Groq Ready",
                }
            ],
            max_tokens=12,
            temperature=0,
        )
        text = response.choices[0].message.content.strip() if response and response.choices else ""
        return {"status": "ok", "message": text or "Groq connected."}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


st.markdown("<h1>🛠️ PromptForge Aggregator</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'>Free Groq-powered prompt optimizer for students 🚀</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("&nbsp;", unsafe_allow_html=True)

    model_options = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
    ]
    selected_model = st.selectbox(
        "Choose model",
        model_options,
        index=0,
        help="Choose faster 8B for testing, 70B for best quality.",
    )
    full_model = f"groq/{selected_model}"
    if "70b" in selected_model:
        st.warning("70B models have lower rate limits on free tier — use 8B for testing!")

    mode = st.radio(
        "Mode",
        ["Coding Agent", "AI Research", "General"],
        index=0,
        help="Coding Agent = strict format & JSON, AI Research = hypothesis & metrics.",
    )

    api_key = get_api_key()
    if not api_key:
        st.error(
            "❌ Missing GROQ_API_KEY — add it to `.streamlit/secrets.toml`:\n\n"
            "```toml\nGROQ_API_KEY = \"your_groq_key_here\"\n```\n\n"
            "Get a free key at [console.groq.com](https://console.groq.com)"
        )
        st.stop()

    st.divider()
    if st.button("🔌 Test Groq Connection"):
        with st.spinner("Checking Groq via litellm..."):
            health = groq_health_check(model=full_model, api_key=api_key)
        if health["status"] == "ok":
            st.success(f"✅ Connected: {health['message']}")
        elif health["status"] == "skipped":
            st.info(health["message"])
        else:
            st.error(f"❌ Connection failed: {health['message']}")

st.subheader("📝 Raw Prompt Input")
raw_prompt = st.text_area(
    "Paste your raw prompt below",
    height=250,
    placeholder="Paste your raw prompt here... e.g. 'Write a Python function to sort a list'",
)
if raw_prompt:
    word_count = len(raw_prompt.split())
    char_count = len(raw_prompt)
    tok_est = estimate_tokens(raw_prompt)
    st.caption(f"Words: {word_count} | Characters: {char_count} | ~{tok_est} tokens")

if st.button("Optimize Now", type="primary"):
    if raw_prompt.strip():
        with st.spinner("Optimizing with Groq (parallel calls)..."):
            api_key = get_api_key()
            if not api_key:
                st.error(
                    "❌ Missing GROQ_API_KEY — add it to `.streamlit/secrets.toml`:\n\n"
                    "```toml\nGROQ_API_KEY = \"your_groq_key_here\"\n```"
                )
                st.stop()

            try:
                # API key is NEVER sent to client — all Groq calls are server-side via LiteLLM
                results = asyncio.run(run_optimizers(raw_prompt, mode, full_model, api_key))

                st.subheader("🎯 Optimized Prompt Variants")
                variant_tabs = st.tabs(["Coding", "Research", "Concise", "Structured"])
                for tab, name in zip(variant_tabs, ["Coding", "Research", "Concise", "Structured"]):
                    with tab:
                        opt = results.get(name, "No output returned.")
                        st.markdown(f"**{name} Prompt**")
                        st.code(opt, language="markdown")
                        st.download_button(
                            f"Copy {name} Prompt",
                            opt,
                            file_name=f"{name.lower()}_prompt.md",
                            mime="text/markdown",
                        )

                winner, scores = asyncio.run(get_winner_and_scores(results, mode, full_model, api_key))
                winner_score = scores.get(winner, "N/A")
                st.subheader(f"🥇 Winner: {winner} (Score: {winner_score}/10)")
                st.code(results.get(winner, "No winner output available."), language="markdown")

                fused = asyncio.run(get_fusion(results, full_model, api_key))
                if fused.startswith("Error:"):
                    if "retries" in fused.lower():
                        st.info("Fusion skipped after rate limit retries — winner is already strong!")
                    else:
                        st.warning(f"Fusion skipped: {fused}")
                else:
                    st.subheader("🌟 Fusion Version (Best Combined)")
                    st.code(fused, language="markdown")
                    original_tokens = estimate_tokens(raw_prompt)
                    fusion_tokens = estimate_tokens(fused)
                    token_delta = original_tokens - fusion_tokens
                    token_label = "Saved" if token_delta > 0 else "Added"
                    st.caption(
                        "Original: ~"
                        f"{original_tokens} tokens | Fusion: ~{fusion_tokens} tokens | "
                        f"{token_label}: {abs(token_delta)}"
                    )
                    st.download_button(
                        "Copy Fusion Prompt",
                        fused,
                        file_name="fusion_prompt.md",
                        mime="text/markdown",
                    )

                st.success("Optimization complete!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Paste a prompt first!")
else:
    st.info("👈 Select your settings, paste a prompt, and click **Optimize Now**.")
