# PromptForge Aggregator - Free Student Edition

A Streamlit app that optimizes prompts for coding agents and AI research using multiple Groq-powered optimizers. Paste once → get 4 variants → smart winner + fusion.

## 🚀 Features

- **4 Optimizers**: 
  - **Coding**: Structured prompts with JSON/YAML output, tool calls, error handling
  - **Research**: Hypothesis-driven prompts with methodology, reproducibility notes, metrics
  - **Concise**: Token-efficient versions preserving 100% intent
  - **Structured**: Perfect structure with role, task, step-by-step instructions, format, constraints, examples

- **AI Judge**: Automatically scores and selects the best variant based on clarity, specificity, token efficiency, and expected performance

- **Fusion**: Combines the best parts of all 4 variants into one ultimate, balanced prompt

- **Free Groq API**: Uses Groq's free tier with Llama 3.1/3.3 models

- **Dark Theme**: Modern, GitHub-inspired dark UI

- **Token Estimates**: Real-time token count estimates and savings calculations

- **Secure**: API keys stored server-side only via Streamlit secrets

## 📋 Prerequisites

- Python 3.8+
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Streamlit (`pip install streamlit`)

## 🛠️ Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ssam-dev/prompt-forge.git
   cd prompt-forge
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key**:
   Create `.streamlit/secrets.toml` in the project root:
   ```toml
   GROQ_API_KEY = "your_groq_key_here"
   ```
   Get your free key at [console.groq.com](https://console.groq.com)

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**:
   The app will open automatically at `http://localhost:8501`

## ☁️ Deployment (Streamlit Cloud - Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `ssam-dev/prompt-forge`
   - Set main file path: `app.py`
   - Click "Advanced settings"
   - Add secret: `GROQ_API_KEY` = `your_groq_key_here`
   - Click "Deploy"

3. **Your app is live!** 🎉

## 🔒 Security Notes

- **API keys are server-side only**: Never exposed to the client browser
- **Streamlit secrets**: Keys stored securely in `.streamlit/secrets.toml` (local) or Streamlit Cloud secrets (production)
- **Never commit keys**: `.gitignore` excludes `.env` and `.streamlit/secrets.toml`
- **No key logging**: No `print()` or `st.write()` statements expose API keys

## ⚙️ Configuration

### Model Selection

- **llama-3.1-8b-instant**: Faster, lower rate limits, good for testing
- **llama-3.3-70b-versatile**: Higher quality, stricter rate limits, best for production

### Mode Options

- **Coding Agent**: Optimizes for structured output, JSON/YAML, tool calls
- **AI Research**: Optimizes for hypothesis, methodology, reproducibility
- **General**: Balanced optimization for general use cases

## 🐛 Known Issues & Limitations

- **Groq Rate Limits**: Free tier has TPM (tokens per minute) limits
  - **Solution**: App includes automatic retry logic with exponential backoff (15s, 30s, 60s, 120s)
  - **Recommendation**: Use `llama-3.1-8b-instant` for heavy testing to avoid rate limits
  - **Note**: Parallel optimizer calls + judge + fusion can exceed limits; retries handle most cases

- **JSON Parsing**: Judge responses may occasionally include markdown formatting
  - **Solution**: Automatic cleaning strips code fences and fixes common JSON issues

- **Token Estimates**: Approximate only (words + chars/4 formula)
  - **Note**: Actual tokenization varies by model; estimates are for comparison purposes

## 🔧 Troubleshooting

### Rate Limit Errors

**Symptoms**: 
- "Rate limit hit" messages in logs
- Optimizations fail or timeout
- "429 Too Many Requests" errors

**Solutions**:
1. **Use the 8B model**: Switch to `llama-3.1-8b-instant` in the sidebar (lower rate limits)
2. **Wait and retry**: The app automatically retries with exponential backoff (15s, 30s, 60s, 120s)
3. **Reduce parallel calls**: The app batches optimizers (2 at a time) with 2-second delays to avoid bursts
4. **Check Groq dashboard**: Visit [console.groq.com](https://console.groq.com) to monitor your TPM usage

**Prevention**:
- Use `llama-3.1-8b-instant` for testing/development
- Wait a few minutes between large optimization runs
- Consider upgrading to Groq Pro tier for higher limits if needed

### JSON Parsing Errors

**Symptoms**:
- Judge returns "Unknown" winner
- Scores show default values (6/10)
- Error messages about JSON parsing

**Solutions**:
1. **Automatic handling**: The app automatically strips markdown code fences (```json) and fixes trailing commas
2. **Retry**: Click "Optimize Now" again - LLM responses vary, next attempt may succeed
3. **Check logs**: If using local deployment, check console for JSON parse warnings

**Technical Details**:
- The `_safe_json_parse` function handles:
  - Markdown code block removal
  - Trailing comma fixes
  - Single-to-double quote conversion
  - Fallback to default scores if parsing fails

### API Key Issues

**Symptoms**:
- "Missing GROQ_API_KEY" error
- App stops immediately after loading

**Solutions**:
1. **Local setup**: Create `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
2. **Streamlit Cloud**: Add secret in app settings → Secrets
3. **Verify key**: Use the "🔌 Test Groq Connection" button in the sidebar
4. **Get new key**: Visit [console.groq.com](https://console.groq.com) if key is invalid

### Other Issues

**App won't start**:
- Check Python version: `python --version` (needs 3.8+)
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`
- Check Streamlit version: `streamlit --version` (should be 1.31.1)

**Optimizations return "Error:" messages**:
- Check API key is valid
- Verify model name is correct (should auto-format as `groq/llama-3.1-8b-instant`)
- Check internet connection
- Review error message for specific issue

## 📊 How It Works

1. **Input**: User pastes raw prompt
2. **Optimization**: 4 parallel Groq calls generate optimized variants
3. **Judging**: AI judge scores each variant and selects winner
4. **Fusion**: Best parts of all variants combined into final prompt
5. **Output**: Display all variants, winner, fusion, and token savings

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available for educational use.

## 👤 Author

Built by **Samarth** in Pune, 2026.

---

**Made with ❤️ using Streamlit, LiteLLM, and Groq**
