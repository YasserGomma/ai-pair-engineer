# AI Pair Engineer

Your AI-powered code review partner. Analyze files or entire projects with multi-model LLM support.

## Summary

**AI Pair Engineer** is an intelligent code analysis tool that augments developer workflows through real-time code review. Unlike simple linters, it leverages multiple AI models via OpenRouter to understand code context and intent. Six specialized modes: **Design Flaw Detection** identifies SOLID violations and architectural issues; **Test Generation** creates comprehensive unit tests with edge cases; **Refactoring** suggests clean code transformations; **Security Audit** performs OWASP Top 10 analysis; **Full Review** provides holistic analysis; **Project Review** analyzes entire codebases for cross-file dependencies and architecture. Built with expert-crafted prompts and a dark-themed Streamlit interface for developers who live in the terminal.

## Features

| Mode | Description |
|------|-------------|
| `design` | SOLID violations, code smells, coupling issues, architectural problems |
| `tests` | Unit tests, edge cases, mocking strategies with runnable code |
| `refactor` | Clean code transformations with before/after comparisons |
| `security` | OWASP Top 10, CVEs, vulnerabilities, remediation priorities |
| `review` | Comprehensive analysis covering all aspects + overall score |
| `project` | **NEW** Multi-file analysis, architecture review, cross-file dependencies |

### Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Model** | OpenAI, Anthropic, Google, Meta, DeepSeek, Qwen via OpenRouter |
| **Project Analysis** | Upload ZIP archives or multiple files for full codebase review |
| **File Upload** | Direct file upload with auto language detection |
| **Cost Tracking** | Real-time token usage and cost estimates before analysis |
| **Persistent Storage** | Code, results, history & settings survive page refreshes |
| **Session History** | Review and compare past analyses (up to 50) |
| **Dark Theme** | Pro hacker theme with Font Awesome icons |

## Quick Start

### Local Installation

```bash
git clone https://github.com/YasserGomma/ai-pair-engineer.git
cd ai-pair-engineer
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Usage

1. **Enter your OpenRouter API key** in the sidebar (get one at [openrouter.ai/keys](https://openrouter.ai/keys))
   - Or set it in `.streamlit/secrets.toml` for local development
   - Or add it to Streamlit Cloud secrets for deployment
2. **Upload a file** or **paste your code** directly
3. **Select language** or use **auto-detect** for uploaded files
4. **Choose your AI model** from OpenAI, Anthropic, Google, Meta, and more
5. **Configure advanced settings** (optional): max tokens, temperature
6. **Choose a review mode** and click Analyze
7. **View cost** per analysis and cumulative session cost
8. **Download the report** as markdown
9. **Review history** of past analyses in the session

## Example

Input this Python code:

```python
def process_user_data(users, filter_type):
    result = []
    for i in range(len(users)):
        user = users[i]
        if filter_type == "active":
            if user["status"] == "active":
                if user["age"] > 18:
                    data = {"name": user["name"], "email": user["email"]}
                    result.append(data)
    return result

def save_to_db(data):
    import sqlite3
    conn = sqlite3.connect("users.db")
    query = f"INSERT INTO users VALUES ('{data['name']}', '{data['email']}')"
    conn.execute(query)
```

The AI Pair Engineer will detect:
- SQL injection vulnerability
- Nested conditionals (code smell)
- Non-Pythonic iteration
- Missing error handling
- Resource leak (unclosed connection)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                             │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  File Review    │    │ Project Review  │   Mode Switcher    │
│  │  - Upload file  │    │ - ZIP upload    │                    │
│  │  - Paste code   │    │ - Multi-file    │                    │
│  └────────┬────────┘    └────────┬────────┘                    │
└───────────┼──────────────────────┼─────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Expert System Prompts                        │
│  design │ tests │ refactor │ security │ review │ project       │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     OpenRouter API Gateway                      │
│  OpenAI │ Anthropic │ Google │ Meta │ DeepSeek │ Qwen          │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │   Markdown Report    │
                    │   + Cost Tracking    │
                    └──────────────────────┘
```

## Supported Models (via OpenRouter)

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o-mini, GPT-4o |
| **Anthropic** | Claude Sonnet 4, Claude 3.5 Haiku |
| **Google** | Gemini 2.0 Flash |
| **Meta** | Llama 3.3 70B Instruct |
| **DeepSeek** | DeepSeek Chat |
| **Qwen** | Qwen 2.5 72B Instruct |

## Supported Languages

Python, JavaScript, TypeScript, Java, Go, Rust, C++, C, C#, Ruby, PHP, SQL, Kotlin, Swift, Scala, R, and more.

## Supported File Types

`.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.java`, `.go`, `.rs`, `.cpp`, `.cc`, `.c`, `.cs`, `.rb`, `.php`, `.sql`, `.kt`, `.swift`, `.scala`, `.r`, `.txt`

## Configuration Options

| Setting | Description |
|---------|-------------|
| API Key | Your OpenRouter API key (required, can be set via Streamlit secrets or environment variables) |
| Language | Programming language or auto-detect from file |
| Context | Additional context for domain-specific feedback |
| Provider | Select AI provider (OpenAI, Anthropic, Google, Meta, DeepSeek, Qwen) |
| Model | Choose from 8+ models with cost information displayed |
| Max Tokens | Maximum length of AI response (1000-8000) |
| Temperature | Controls randomness (0.0 = focused, 1.0 = creative) |

### Model Selection

The app now features **grouped model selection by provider** for better UX:
- Select a provider first (e.g., OpenAI, Anthropic)
- Then choose a specific model from that provider
- Cost information is displayed next to each model name
- Estimated cost is shown before running analysis

## Cost Tracking

The app tracks API usage in real-time via OpenRouter with **pre-analysis cost estimates**:

### Supported Models & Pricing

| Provider | Model | Input Cost | Output Cost | Est. per Review |
|----------|-------|------------|-------------|-----------------|
| **OpenAI** | GPT-4o-mini | $0.15/1M | $0.60/1M | ~$0.001 |
| **OpenAI** | GPT-4o | $2.50/1M | $10.00/1M | ~$0.02 |
| **Anthropic** | Claude Sonnet 4 | $3.00/1M | $15.00/1M | ~$0.025 |
| **Anthropic** | Claude 3.5 Haiku | $0.80/1M | $4.00/1M | ~$0.005 |
| **Google** | Gemini 2.0 Flash | $0.10/1M | $0.40/1M | ~$0.001 |
| **Meta** | Llama 3.3 70B | $0.40/1M | $0.40/1M | ~$0.001 |
| **DeepSeek** | DeepSeek Chat | $0.14/1M | $0.28/1M | ~$0.001 |
| **Qwen** | Qwen 2.5 72B | $0.35/1M | $0.40/1M | ~$0.001 |

### Cost Features

- **Pre-analysis estimates**: See estimated cost before running analysis
- **Real-time tracking**: Track token usage and costs during session
- **Session summary**: View total tokens and cost for all analyses
- **Per-model pricing**: Cost information displayed with each model

## Technical Details

- **Framework**: Streamlit 1.28+
- **API Gateway**: OpenRouter (access to 100+ models via single API)
- **Default Model**: openai/gpt-4o-mini (cost-effective)
- **Model Selection**: Grouped by provider with cost indicators
- **Cost Estimation**: Pre-analysis cost estimates based on code length
- **Prompt Engineering**: Mode-specific expert prompts with structured output
- **Response Time**: ~5 seconds per analysis
- **Input Validation**: Code length limits (10-50,000 characters), file size limits (500KB)
- **Error Handling**: Comprehensive error messages for API issues
- **Security**: API key validation (supports secrets, env vars, manual input)
- **Persistent Storage**: JSON-based storage in `.data/` directory (history, results, settings)
- **Dependencies**: streamlit, openai, python-dotenv

## Why This Approach?

1. **Multi-Model Access**: OpenRouter provides access to OpenAI, Anthropic, Google, Meta, and more through a single API
2. **Specialized Prompts**: Each mode has a carefully crafted system prompt that acts as a domain expert
3. **Structured Output**: Consistent markdown formatting makes reports actionable
4. **Context-Aware**: Additional context improves relevance (e.g., "security-critical", "high-performance")
5. **Cost Transparency**: Real-time cost tracking helps manage API expenses
6. **File Support**: Direct file upload reduces friction and enables auto-detection
7. **Session History**: Review and compare past analyses without re-running
8. **Accessible**: No installation required when deployed to Streamlit Cloud
9. **Extensible**: Easy to add new models or languages


