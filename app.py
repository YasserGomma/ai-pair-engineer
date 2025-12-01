"""AI Pair Engineer - Intelligent code analysis powered by multiple LLM providers."""

import streamlit as st
from openai import OpenAI
from enum import Enum
from typing import Optional, Tuple, Dict, List
from pathlib import Path
import zipfile
import io
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
from ui_components import load_font_awesome, icon, Icons, render_icon_text
import storage

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Pair Engineer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_font_awesome()


def load_css() -> None:
    """Load external CSS file."""
    try:
        with open("assets/styles.css", "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown("<style>/* Fallback */</style>", unsafe_allow_html=True)


def load_mobile_scripts() -> None:
    """Load mobile-specific scripts for better UX."""
    st.markdown("""
    <script>
    (function() {
        function setupMobileSidebar() {
            const isMobile = window.innerWidth <= 768;
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            const toggleButton = document.querySelector('button[data-testid="baseButton-header"]');
            
            if (isMobile && sidebar) {
                let overlay = document.querySelector('.sidebar-overlay');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.className = 'sidebar-overlay';
                    document.body.appendChild(overlay);
                }
                
                if (toggleButton) {
                    toggleButton.style.display = 'flex';
                    toggleButton.style.zIndex = '1000';
                    toggleButton.style.position = 'fixed';
                    toggleButton.style.top = '1rem';
                    toggleButton.style.left = '1rem';
                }
                
                function updateOverlay() {
                    const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
                    if (isExpanded) {
                        overlay.classList.add('active');
                        document.body.style.overflow = 'hidden';
                    } else {
                        overlay.classList.remove('active');
                        document.body.style.overflow = '';
                    }
                }
                
                overlay.addEventListener('click', () => {
                    if (toggleButton && sidebar.getAttribute('aria-expanded') === 'true') {
                        toggleButton.click();
                    }
                });
                
                const observer = new MutationObserver(() => {
                    updateOverlay();
                });
                
                observer.observe(sidebar, {
                    attributes: true,
                    attributeFilter: ['aria-expanded']
                });
                
                updateOverlay();
            }
        }
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', setupMobileSidebar);
        } else {
            setupMobileSidebar();
        }
        
        window.addEventListener('resize', setupMobileSidebar);
        
        const inputs = document.querySelectorAll('input[type="text"], input[type="password"], textarea, select');
        inputs.forEach(input => {
            if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
                input.style.fontSize = '16px';
            }
        });
    })();
    </script>
    """, unsafe_allow_html=True)


load_css()
load_mobile_scripts()

MIN_CODE_LENGTH = 10
MAX_CODE_LENGTH = 100000
DEFAULT_MAX_TOKENS = 4000
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_PROJECT_FILES = 50
MAX_PROJECT_SIZE = 500 * 1024

SUPPORTED_MODELS = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3-5-haiku",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "deepseek/deepseek-chat",
    "qwen/qwen-2.5-72b-instruct",
]

EXTENSION_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".jsx": "javascript", ".java": "java", ".go": "go", ".rs": "rust",
    ".cpp": "c++", ".cc": "c++", ".c": "c", ".cs": "c#", ".rb": "ruby",
    ".php": "php", ".sql": "sql", ".kt": "kotlin", ".swift": "swift",
    ".scala": "scala", ".r": "r", ".R": "r",
}

SUPPORTED_FILE_TYPES = ["py", "js", "ts", "tsx", "jsx", "java", "go", "rs", "cpp", "cc", "c", "cs", "rb", "php", "sql", "kt", "swift", "scala", "r", "txt"]

MODEL_COSTS = {
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "anthropic/claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "anthropic/claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "google/gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
    "meta-llama/llama-3.3-70b-instruct": {"input": 0.40, "output": 0.40},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "qwen/qwen-2.5-72b-instruct": {"input": 0.35, "output": 0.40},
}

MODEL_GROUPS = {
    "OpenAI": ["openai/gpt-4o-mini", "openai/gpt-4o"],
    "Anthropic": ["anthropic/claude-sonnet-4", "anthropic/claude-3-5-haiku"],
    "Google": ["google/gemini-2.0-flash-001"],
    "Meta": ["meta-llama/llama-3.3-70b-instruct"],
    "DeepSeek": ["deepseek/deepseek-chat"],
    "Qwen": ["qwen/qwen-2.5-72b-instruct"],
}

MODEL_DISPLAY_NAMES = {
    "openai/gpt-4o-mini": "GPT-4o-mini",
    "openai/gpt-4o": "GPT-4o",
    "anthropic/claude-sonnet-4": "Claude Sonnet 4",
    "anthropic/claude-3-5-haiku": "Claude 3.5 Haiku",
    "google/gemini-2.0-flash-001": "Gemini 2.0 Flash",
    "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B",
    "deepseek/deepseek-chat": "DeepSeek Chat",
    "qwen/qwen-2.5-72b-instruct": "Qwen 2.5 72B",
}

IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env', '.idea', '.vscode', 'dist', 'build', '.next', 'coverage'}
IGNORE_FILES = {'.DS_Store', 'package-lock.json', 'yarn.lock', 'Pipfile.lock'}

EXAMPLE_CODE = '''def process_user_data(users, filter_type):
    result = []
    for i in range(len(users)):
        user = users[i]
        if filter_type == "active":
            if user["status"] == "active":
                if user["age"] > 18:
                    data = {"name": user["name"], "email": user["email"], "age": user["age"]}
                    result.append(data)
        elif filter_type == "premium":
            if user["plan"] == "premium":
                data = {"name": user["name"], "email": user["email"], "plan": user["plan"]}
                result.append(data)
    return result

def save_to_db(data):
    import sqlite3
    conn = sqlite3.connect("users.db")
    query = f"INSERT INTO users VALUES ('{data['name']}', '{data['email']}')"
    conn.execute(query)
    conn.commit()
'''


class ReviewMode(Enum):
    """Enumeration of available review modes."""
    DESIGN_FLAWS = "Design Flaw Detection"
    TEST_GENERATION = "Test Generation"
    REFACTORING = "Refactoring Suggestions"
    SECURITY_REVIEW = "Security Audit"
    FULL_REVIEW = "Full Pair Review"
    PROJECT_REVIEW = "Project Review"


class SessionStateManager:
    """Manages Streamlit session state with persistent storage."""

    @staticmethod
    def init() -> None:
        if "initialized" not in st.session_state:
            st.session_state.history = storage.load_history()
            st.session_state.total_tokens = storage.get_tokens()
            st.session_state.total_cost = storage.get_cost()
            for mode_name, result in storage.load_results().items():
                st.session_state[f"result_{mode_name}"] = result
            st.session_state.code_input = storage.get_code_input()
            st.session_state.review_mode = storage.get_review_mode()
            st.session_state.analysis_mode = storage.get_analysis_mode()
            st.session_state.api_key = ""
            st.session_state.initialized = True

    @staticmethod
    def get_history() -> list:
        return st.session_state.get("history", [])

    @staticmethod
    def add_to_history(entry: dict) -> None:
        st.session_state.history = storage.add_history_entry(entry)

    @staticmethod
    def clear_history() -> None:
        st.session_state.history = []
        storage.clear_history()
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("history_expanded_") or key.startswith("show_history_result_")]
        for key in keys_to_remove:
            del st.session_state[key]

    @staticmethod
    def get_tokens() -> Dict[str, int]:
        return st.session_state.get("total_tokens", {"input": 0, "output": 0})

    @staticmethod
    def add_tokens(input_tokens: int, output_tokens: int) -> None:
        if "total_tokens" not in st.session_state:
            st.session_state.total_tokens = {"input": 0, "output": 0}
        st.session_state.total_tokens["input"] += input_tokens
        st.session_state.total_tokens["output"] += output_tokens
        storage.add_tokens(input_tokens, output_tokens)

    @staticmethod
    def get_cost() -> float:
        return st.session_state.get("total_cost", 0.0)

    @staticmethod
    def add_cost(cost: float) -> None:
        st.session_state.total_cost += cost
        storage.add_cost(cost)

    @staticmethod
    def reset_cost_tracker() -> None:
        st.session_state.total_tokens = {"input": 0, "output": 0}
        st.session_state.total_cost = 0.0
        storage.reset_cost_tracker()

    @staticmethod
    def get_result(mode_name: str) -> Optional[str]:
        return st.session_state.get(f"result_{mode_name}")

    @staticmethod
    def set_result(mode_name: str, result: str) -> None:
        st.session_state[f"result_{mode_name}"] = result
        storage.save_result(mode_name, result)

    @staticmethod
    def clear_result(mode_name: str) -> None:
        if f"result_{mode_name}" in st.session_state:
            del st.session_state[f"result_{mode_name}"]
        storage.clear_result(mode_name)

    @staticmethod
    def clear_all_results() -> None:
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("result_")]
        for key in keys_to_remove:
            del st.session_state[key]
        storage.clear_all_results()


class APIError(Exception):
    pass


class AuthenticationError(APIError):
    pass


class RateLimitError(APIError):
    pass


class QuotaExceededError(APIError):
    pass


class TimeoutError(APIError):
    pass


class OpenRouterClient:
    """Handles OpenRouter API interactions."""

    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)

    def analyze_code(self, code: str, language: str, mode: ReviewMode, context: str = "", model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS, temperature: float = DEFAULT_TEMPERATURE) -> Tuple[str, Dict[str, int]]:
        user_message = f"Please analyze this {language} code:\n\n```{language}\n{code}\n```"
        if context:
            user_message += f"\nAdditional context: {context}"

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": SYSTEM_PROMPTS[mode]}, {"role": "user", "content": user_message}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            result = response.choices[0].message.content
            if not result:
                raise APIError("Received empty response from API")
            tokens = {"input": response.usage.prompt_tokens if response.usage else 0, "output": response.usage.completion_tokens if response.usage else 0}
            return result, tokens
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "invalid" in error_msg or "api key" in error_msg:
                raise AuthenticationError("Authentication failed. Please check your OpenRouter API key.")
            elif "rate limit" in error_msg:
                raise RateLimitError("Rate limit exceeded. Please wait a moment and try again.")
            elif "quota" in error_msg or "billing" in error_msg or "credit" in error_msg:
                raise QuotaExceededError("Quota exceeded. Please check your OpenRouter account credits.")
            elif "timeout" in error_msg:
                raise TimeoutError("Request timed out. Please try again.")
            else:
                raise APIError(f"Error: {str(e)}. Please try again or check your connection.")


SYSTEM_PROMPTS = {
    ReviewMode.DESIGN_FLAWS: """You are an expert software architect. Analyze the code for design flaws.
Focus on: SOLID violations, code smells, coupling/cohesion issues, missing abstractions, error handling gaps, security vulnerabilities, performance anti-patterns.
Format: ## 🔍 Design Flaws Detected
### Critical Issues / ### Warnings / ### Suggestions / ## 💡 Recommended Actions""",

    ReviewMode.TEST_GENERATION: """You are an expert test engineer. Generate comprehensive tests.
Include: Unit tests, edge cases, error scenarios, integration test suggestions, mocking strategies.
Format: ## 🧪 Generated Tests with runnable code, edge cases, mocking strategy, coverage notes.""",

    ReviewMode.REFACTORING: """You are an expert in clean code. Provide refactoring suggestions.
Consider: Readability, DRY, function extraction, naming, simplification, modern features, design patterns.
Format: ## ♻️ Refactoring Recommendations with before/after, quick wins, larger refactors, complete refactored code.""",

    ReviewMode.SECURITY_REVIEW: """You are a cybersecurity expert. Conduct a thorough security audit.
Focus on: Injection vulnerabilities, auth issues, data exposure, crypto failures, input validation, misconfigurations, vulnerable dependencies, business logic flaws.
Format: ## 🔒 Security Audit Report with Critical/High/Medium/Low issues, compliance notes, remediation priority, security strengths.""",

    ReviewMode.FULL_REVIEW: """You are an AI Pair Engineer. Provide comprehensive code review.
Include: First impression, design analysis, bug detection, security scan, performance review, test suggestions, refactoring ideas, positive notes.
Format: ## 🤖 AI Pair Engineer Review with Overall Score, What's Working Well, Potential Bugs, Design Concerns, Security Notes, Performance Tips, Suggested Tests, Refactoring Opportunities, Priority Actions.""",

    ReviewMode.PROJECT_REVIEW: """You are an AI Pair Engineer analyzing an entire project.
Analyze holistically: Project structure, architecture, code quality, security, performance, testing, best practices, documentation.
Format: ## 🤖 AI Pair Engineer Review
### 📊 Overall Score: [X/10]
### 📁 Project Structure Analysis
### ✅ What's Working Well
### 🐛 Potential Bugs (with file references)
### 🏗️ Design Concerns
### 🔒 Security Notes
### ⚡ Performance Tips
### 🧪 Suggested Tests
### ♻️ Refactoring Opportunities (with file references)
### 🎯 Priority Actions (top 3-5, ordered by impact)"""
}


def init_session_state() -> None:
    SessionStateManager.init()


def scan_project_files(uploaded_files: List) -> Tuple[Dict[str, str], List[str]]:
    files_content = {}
    errors = []
    total_size = 0
    for uploaded_file in uploaded_files:
        try:
            file_size = len(uploaded_file.getvalue())
            total_size += file_size
            if total_size > MAX_PROJECT_SIZE:
                errors.append(f"Total size exceeds {MAX_PROJECT_SIZE // 1024}KB limit")
                break
            if len(files_content) >= MAX_PROJECT_FILES:
                errors.append(f"Maximum {MAX_PROJECT_FILES} files limit reached")
                break
            if uploaded_file.name in IGNORE_FILES:
                continue
            ext = Path(uploaded_file.name).suffix.lower()
            if ext.lstrip('.') not in SUPPORTED_FILE_TYPES:
                continue
            try:
                content = uploaded_file.read().decode("utf-8")
                uploaded_file.seek(0)
                files_content[uploaded_file.name] = content
            except UnicodeDecodeError:
                errors.append(f"Could not read {uploaded_file.name} (not UTF-8)")
        except Exception as e:
            errors.append(f"Error reading {uploaded_file.name}: {str(e)}")
    return files_content, errors


def extract_zip_files(zip_file) -> Tuple[Dict[str, str], List[str]]:
    files_content = {}
    errors = []
    total_size = 0
    try:
        with zipfile.ZipFile(io.BytesIO(zip_file.getvalue()), 'r') as zf:
            for file_info in zf.infolist():
                if file_info.is_dir():
                    continue
                path_parts = Path(file_info.filename).parts
                if any(part in IGNORE_DIRS for part in path_parts):
                    continue
                filename = Path(file_info.filename).name
                if filename in IGNORE_FILES or filename.startswith('.'):
                    continue
                ext = Path(filename).suffix.lower()
                if ext.lstrip('.') not in SUPPORTED_FILE_TYPES:
                    continue
                total_size += file_info.file_size
                if total_size > MAX_PROJECT_SIZE:
                    errors.append(f"Total size exceeds {MAX_PROJECT_SIZE // 1024}KB limit")
                    break
                if len(files_content) >= MAX_PROJECT_FILES:
                    errors.append(f"Maximum {MAX_PROJECT_FILES} files limit reached")
                    break
                try:
                    with zf.open(file_info.filename) as f:
                        content = f.read().decode("utf-8")
                        files_content[file_info.filename] = content
                except UnicodeDecodeError:
                    errors.append(f"Could not read {file_info.filename} (not UTF-8)")
    except zipfile.BadZipFile:
        errors.append("Invalid or corrupted zip file")
    except Exception as e:
        errors.append(f"Error processing zip file: {str(e)}")
    return files_content, errors


def format_project_for_review(files_content: Dict[str, str]) -> str:
    parts = [f"# Project Analysis Request\n**Total Files:** {len(files_content)}\n---\n"]
    for filepath, content in sorted(files_content.items()):
        ext = Path(filepath).suffix.lower()
        lang = EXTENSION_TO_LANGUAGE.get(ext, "text")
        lines = len(content.split('\n'))
        parts.append(f"\n## File: `{filepath}`\n**Language:** {lang} | **Lines:** {lines}\n```{lang}\n{content}\n```\n")
    return "\n".join(parts)


def get_project_stats(files_content: Dict[str, str]) -> Dict:
    stats = {"total_files": len(files_content), "total_lines": 0, "total_chars": 0, "languages": {}, "files_by_type": {}}
    for filepath, content in files_content.items():
        ext = Path(filepath).suffix.lower()
        lang = EXTENSION_TO_LANGUAGE.get(ext, "other")
        lines = len(content.split('\n'))
        chars = len(content)
        stats["total_lines"] += lines
        stats["total_chars"] += chars
        stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
        stats["files_by_type"][ext] = stats["files_by_type"].get(ext, 0) + 1
    return stats


def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    costs = MODEL_COSTS.get(model, MODEL_COSTS[DEFAULT_MODEL])
    return (input_tokens / 1_000_000) * costs["input"] + (output_tokens / 1_000_000) * costs["output"]


def estimate_cost(code_length: int, model: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> Dict[str, float]:
    estimated_input_tokens = int(code_length / 4) + 500
    estimated_output_tokens = min(max_tokens, int(estimated_input_tokens * 0.5))
    return {"input_tokens": estimated_input_tokens, "output_tokens": estimated_output_tokens, "cost": calculate_cost(estimated_input_tokens, estimated_output_tokens, model)}


def get_model_cost_info(model: str) -> str:
    costs = MODEL_COSTS.get(model)
    if not costs:
        return "Cost: Unknown"
    est_1k_cost = ((1000 / 1_000_000) * costs["input"]) + ((500 / 1_000_000) * costs["output"])
    return f"~${est_1k_cost:.4f}/1K tokens" if est_1k_cost >= 0.001 else f"~${est_1k_cost*1000:.2f}/1K tokens"


def detect_language_from_extension(filename: str) -> Optional[str]:
    for ext, lang in EXTENSION_TO_LANGUAGE.items():
        if filename.lower().endswith(ext):
            return lang
    return None


def add_to_history(code_snippet: str, language: str, mode: ReviewMode, result: str, tokens: Dict[str, int], cost: float, model: str) -> None:
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "code_preview": code_snippet[:100] + "..." if len(code_snippet) > 100 else code_snippet,
        "language": language, "mode": mode.value, "result": result, "tokens": tokens, "cost": cost, "model": model
    }
    SessionStateManager.add_to_history(entry)


def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty"
    api_key = api_key.strip()
    if not api_key.startswith("sk-or-"):
        return False, "OpenRouter API key should start with 'sk-or-'"
    if len(api_key) < 30:
        return False, "API key appears to be too short"
    return True, None


def validate_code_input(code: str) -> Tuple[bool, Optional[str]]:
    if not code or not code.strip():
        return False, "Code input cannot be empty"
    code = code.strip()
    if len(code) < MIN_CODE_LENGTH:
        return False, f"Code is too short (minimum {MIN_CODE_LENGTH} characters)"
    if len(code) > MAX_CODE_LENGTH:
        return False, f"Code is too long (maximum {MAX_CODE_LENGTH} characters)"
    return True, None


def render_header() -> None:
    st.markdown(f'<p class="main-header">{icon(Icons.TERMINAL, "1em")} AI Pair Engineer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent code analysis powered by multiple LLM providers</p>', unsafe_allow_html=True)
    st.divider()


def _render_api_key_input() -> str:
    st.markdown("""
    <style>
    .api-key-wrapper {
        margin-bottom: 1rem;
    }
    
    .api-key-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    
    .api-key-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.9rem;
    }
    
    .api-key-help {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: rgba(88, 166, 255, 0.1);
        border: 1px solid rgba(88, 166, 255, 0.2);
        color: var(--accent-primary);
        font-size: 0.65rem;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: help;
    }
    
    div[data-testid="stTextInput"] input[type="password"],
    div[data-testid="stTextInput"] input[type="text"],
    div[data-testid="stTextInput"] input:not([type]) {
        font-family: var(--font-mono) !important;
        letter-spacing: 0.05em !important;
        height: 40px !important;
        padding: 0.625rem 0.875rem !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
    }
    
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.1) !important;
        outline: none !important;
    }
    
    div[data-testid="stTextInput"] button:not([key]) {
        display: none !important;
    }
    
    button[key="toggle_api_key_visibility"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-primary) !important;
        color: var(--text-secondary) !important;
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        min-height: 40px !important;
        padding: 0 !important;
        border-radius: var(--radius-md) !important;
        transition: all 0.2s !important;
        font-size: 1rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    button[key="toggle_api_key_visibility"]:hover {
        background: var(--bg-elevated) !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }
    
    .api-key-status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.625rem;
        border-radius: var(--radius-sm);
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    
    .api-key-status.valid {
        background: rgba(126, 231, 135, 0.1);
        border: 1px solid rgba(126, 231, 135, 0.2);
        color: var(--accent-secondary);
    }
    
    .api-key-status.invalid {
        background: rgba(248, 81, 73, 0.1);
        border: 1px solid rgba(248, 81, 73, 0.2);
        color: var(--accent-error);
    }
    
    .api-key-link {
        color: var(--accent-primary);
        text-decoration: none;
        font-size: 0.8rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        margin-top: 0.5rem;
        transition: all 0.2s;
    }
    
    .api-key-link:hover {
        color: var(--accent-purple);
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)
    
    api_key = ""
    api_key_source = None
    
    # Check for API key in secrets
    try:
        if "OPENROUTER_API_KEY" in st.secrets:
            api_key = st.secrets["OPENROUTER_API_KEY"]
            api_key_source = "secrets"
    except Exception:
        pass
    
    # Check for API key in environment
    if not api_key and os.getenv("OPENROUTER_API_KEY"):
        api_key = os.getenv("OPENROUTER_API_KEY")
        api_key_source = "environment"
    
    st.markdown("""
    <div class="api-key-wrapper">
        <div class="api-key-header">
            <div class="api-key-title">
                <i class="fas fa-key" style="color: var(--accent-primary); font-size: 0.85rem;"></i>
                <span>OpenRouter API Key</span>
            </div>
            <div class="api-key-help" title="Get your API key from openrouter.ai/keys">?</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if api_key_source:
        status_icon = icon(Icons.CHECK, "0.85em", "#7ee787")
        st.markdown(f"""
        <div class="api-key-status valid">
            {status_icon} Using API key from {api_key_source}
        </div>
        """, unsafe_allow_html=True)
    else:
        current_key = st.session_state.get("api_key", "")
        if "api_key_visible" not in st.session_state:
            st.session_state.api_key_visible = False
        
        input_col, toggle_col = st.columns([6, 1], gap="small")
        
        with input_col:
            api_key = st.text_input(
                "OpenRouter API Key",
                type="password" if not st.session_state.api_key_visible else "default",
                value=current_key,
                placeholder="sk-or-v1-...",
                help="",
                label_visibility="collapsed",
                key="api_key_input"
            )
        
        with toggle_col:
            toggle_text = "🙈" if st.session_state.api_key_visible else "👁️"
            if st.button(toggle_text, key="toggle_api_key_visibility", help="Toggle visibility"):
                st.session_state.api_key_visible = not st.session_state.api_key_visible
                if api_key:
                    st.session_state["api_key"] = api_key
                st.rerun()
        
        if api_key:
            is_valid, error_msg = validate_api_key(api_key)
            if is_valid:
                status_icon = icon(Icons.CHECK, "0.85em", "#7ee787")
                st.markdown(f"""
                <div class="api-key-status valid">
                    {status_icon} Valid format
                </div>
                """, unsafe_allow_html=True)
            else:
                status_icon = icon(Icons.EXCLAMATION, "0.85em", "#f85149")
                st.markdown(f"""
                <div class="api-key-status invalid">
                    {status_icon} {error_msg}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
        <a href="https://openrouter.ai/keys" target="_blank" class="api-key-link">
            <i class="fas fa-external-link-alt" style="font-size: 0.75rem;"></i>
            Get API key
        </a>
        """, unsafe_allow_html=True)
        
        if api_key != current_key:
            st.session_state["api_key"] = api_key
    
    return api_key


def _render_language_context() -> Tuple[str, str]:
    language = st.selectbox("Programming Language", ["auto-detect", "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#", "ruby", "php", "sql", "kotlin", "swift", "other"], index=0)
    context = st.text_area("Additional Context (optional)", placeholder="E.g., 'This is part of a payment processing system'", height=100)
    return language, context


def _render_model_settings() -> Tuple[str, int, float]:
    st.markdown(f"### {icon(Icons.SETTINGS, '1em')} Advanced Settings", unsafe_allow_html=True)
    selected_provider = st.selectbox("Provider", list(MODEL_GROUPS.keys()), index=0)
    provider_models = MODEL_GROUPS[selected_provider]
    model_options = [f"{MODEL_DISPLAY_NAMES.get(m, m.split('/')[-1])} ({get_model_cost_info(m)})" for m in provider_models]
    default_idx = provider_models.index(DEFAULT_MODEL) if DEFAULT_MODEL in provider_models else 0
    selected_display = st.selectbox("Model", model_options, index=default_idx)
    model = provider_models[model_options.index(selected_display)]
    max_tokens = st.slider("Max Tokens", 1000, 8000, DEFAULT_MAX_TOKENS, 500)
    temperature = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, 0.1)
    return model, max_tokens, temperature


def _render_cost_tracker() -> None:
    st.markdown(f"### {icon(Icons.DOLLAR, '1em')} Session Cost Tracker", unsafe_allow_html=True)
    tokens = SessionStateManager.get_tokens()
    total_cost = SessionStateManager.get_cost()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Input Tokens", f"{tokens.get('input', 0):,}")
    with col2:
        st.metric("Output Tokens", f"{tokens.get('output', 0):,}")
    st.metric("Total Cost", f"${total_cost:.4f}")
    if st.button("Reset Cost Tracker", key="reset_cost", use_container_width=True):
        SessionStateManager.reset_cost_tracker()
        st.rerun()


def _render_sidebar_footer() -> None:
    st.markdown(f"### {icon(Icons.INFO, '1em')} Tips\n- Upload files or paste code\n- Use **auto-detect** for files\n- Add context for better feedback", unsafe_allow_html=True)
    st.divider()
    if st.button("Clear All Results", key="clear_results", use_container_width=True):
        SessionStateManager.clear_all_results()
        st.success("Results cleared!")
        st.rerun()


def render_sidebar() -> Tuple[str, str, str, str, int, float]:
    with st.sidebar:
        st.markdown(f"## {icon(Icons.GEAR, '1em')} Configuration", unsafe_allow_html=True)
        api_key = _render_api_key_input()
        st.divider()
        language, context = _render_language_context()
        st.divider()
        model, max_tokens, temperature = _render_model_settings()
        st.divider()
        _render_cost_tracker()
        st.divider()
        _render_sidebar_footer()
    return api_key, language, context, model, max_tokens, temperature


def render_code_input() -> Tuple[str, Optional[str]]:
    st.markdown(f"### {icon(Icons.FILE, '1em')} Your Code", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a code file", type=SUPPORTED_FILE_TYPES)
    detected_language = None
    file_just_uploaded = False
    if uploaded_file is not None:
        file_size = len(uploaded_file.getvalue())
        if file_size > 500 * 1024:
            st.error(f"File too large ({file_size / 1024:.1f}KB). Maximum size is 500KB.")
        else:
            try:
                file_content = uploaded_file.read().decode("utf-8")
                # Check if this is a new file upload
                if st.session_state.get("code_input", "") != file_content:
                    st.session_state["code_input"] = file_content
                    storage.save_code_input(file_content)
                    file_just_uploaded = True
                detected_language = detect_language_from_extension(uploaded_file.name)
                st.success(f"Loaded `{uploaded_file.name}`" + (f" - Detected: **{detected_language}**" if detected_language else ""))
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    st.markdown("**Or paste your code below:**")
    code_input = st.text_area("Paste your code here", height=350, placeholder="Paste your code here...", label_visibility="collapsed", value=st.session_state.get("code_input", ""), key="code_text_area")
    # Use session state value if file was just uploaded (text_area may have stale value)
    if file_just_uploaded:
        code_input = st.session_state.get("code_input", "")
    elif code_input != st.session_state.get("code_input", ""):
        st.session_state["code_input"] = code_input
        storage.save_code_input(code_input)
    if code_input:
        st.caption(f"**{len(code_input.split(chr(10)))}** lines | **{len(code_input):,}** characters")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Example Code", use_container_width=True):
            st.session_state["code_input"] = EXAMPLE_CODE
            storage.save_code_input(EXAMPLE_CODE)
            st.rerun()
    with col2:
        if st.button("Clear Code", use_container_width=True):
            st.session_state["code_input"] = ""
            storage.save_code_input("")
            st.rerun()
    return code_input, detected_language


def render_project_input() -> Tuple[Dict[str, str], List[str]]:
    st.markdown(f"### {icon(Icons.FOLDER, '1em')} Your Project", unsafe_allow_html=True)

    upload_option = st.radio("Upload method:", ["Multiple Files", "ZIP Archive"], horizontal=True, key="project_upload_method")
    project_files = {}
    upload_errors = []

    if upload_option == "Multiple Files":
        uploaded_files = st.file_uploader("Select project files", type=SUPPORTED_FILE_TYPES, accept_multiple_files=True, key="project_files_uploader")
        if uploaded_files:
            project_files, upload_errors = scan_project_files(uploaded_files)
    else:
        zip_file = st.file_uploader("Upload ZIP archive", type=["zip"], key="project_zip_uploader")
        if zip_file:
            project_files, upload_errors = extract_zip_files(zip_file)

    for error in upload_errors:
        st.warning(error)

    if project_files:
        stats = get_project_stats(project_files)
        st.markdown("---")
        st.markdown(f"### {icon(Icons.CHART, '1em', '#10b981')} Project Statistics", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Files", stats["total_files"])
        with col2:
            st.metric("Lines", f"{stats['total_lines']:,}")
        with col3:
            st.metric("Characters", f"{stats['total_chars']:,}")

        if stats["languages"]:
            st.markdown(f"**Languages:** {', '.join([f'{l}: {c}' for l, c in sorted(stats['languages'].items())])}")

        with st.expander(f"View {len(project_files)} files"):
            for fp in sorted(project_files.keys()):
                ext = Path(fp).suffix.lower()
                lang = EXTENSION_TO_LANGUAGE.get(ext, "text")
                st.markdown(f"- `{fp}` ({lang}, {len(project_files[fp].split(chr(10)))} lines)")

        if st.button("Clear Project", use_container_width=True):
            st.session_state.pop("project_files_uploader", None)
            st.session_state.pop("project_zip_uploader", None)
            st.rerun()
    else:
        st.markdown(f"{icon(Icons.INFO, '1em', '#58a6ff')} Upload project files or a ZIP archive to analyze.", unsafe_allow_html=True)

    return project_files, upload_errors


def render_history() -> None:
    history = SessionStateManager.get_history()
    if not history:
        return
    st.markdown(f"### {icon(Icons.HISTORY, '1em')} Session History", unsafe_allow_html=True)
    for i, entry in enumerate(history):
        with st.expander(f"{entry['timestamp']} | {entry['mode']} | {entry['language']} | ${entry['cost']:.4f}"):
            st.markdown(f"**Code Preview:**\n```\n{entry['code_preview']}\n```")
            st.markdown(f"**Model:** {entry['model']} | **Tokens:** {entry['tokens']['input']} in / {entry['tokens']['output']} out")
            if st.button(f"View Full Result", key=f"view_{i}"):
                st.markdown("---")
                st.markdown(entry['result'])
    if st.button("Clear History", use_container_width=True):
        SessionStateManager.clear_history()
        st.rerun()


def _get_mode_description(mode: ReviewMode) -> str:
    descriptions = {
        ReviewMode.DESIGN_FLAWS: "Detect SOLID violations, code smells, and architectural issues",
        ReviewMode.TEST_GENERATION: "Generate unit tests, edge cases, and mocking strategies",
        ReviewMode.REFACTORING: "Get clean code suggestions and refactored examples",
        ReviewMode.SECURITY_REVIEW: "Comprehensive security audit: vulnerabilities, OWASP Top 10",
        ReviewMode.FULL_REVIEW: "Comprehensive review covering all aspects",
        ReviewMode.PROJECT_REVIEW: "Analyze entire project: structure, architecture, cross-file dependencies"
    }
    return descriptions.get(mode, "")


def _execute_analysis(api_key: str, code_input: str, language: str, mode: ReviewMode, context: str, model: str, max_tokens: int, temperature: float) -> None:
    with st.spinner(f"Analyzing code for {mode.value.lower()}..."):
        try:
            client = OpenRouterClient(api_key)
            result, tokens = client.analyze_code(code_input, language, mode, context, model, max_tokens, temperature)
            SessionStateManager.set_result(mode.name, result)
            cost = calculate_cost(tokens.get("input", 0), tokens.get("output", 0), model)
            SessionStateManager.add_tokens(tokens.get("input", 0), tokens.get("output", 0))
            SessionStateManager.add_cost(cost)
            add_to_history(code_input, language, mode, result, tokens, cost, model)
            st.rerun()
        except (AuthenticationError, RateLimitError, QuotaExceededError, TimeoutError, APIError) as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")


def _render_mode_result(mode: ReviewMode) -> None:
    """Render analysis results with enhanced styling."""
    result = SessionStateManager.get_result(mode.name)
    if result:
        st.markdown("---")
        st.markdown("""
        <div style="background: var(--bg-card); border: 1px solid var(--border-primary); 
                    border-radius: var(--radius-lg); padding: 1.5rem; margin: 1rem 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                <h4 style="margin: 0; color: var(--text-primary); display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-check-circle" style="color: var(--accent-secondary);"></i>
                    Analysis Results
                </h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Result content
        st.markdown(result)
        
        # Action buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button(
                "Download Report",
                result,
                file_name=f"{mode.name.lower()}_report.md",
                mime="text/markdown",
                key=f"download_{mode.name}",
                use_container_width=True
            )
        with col2:
            if st.button("Clear Result", key=f"clear_{mode.name}", use_container_width=True):
                SessionStateManager.clear_result(mode.name)
                st.rerun()


def _resolve_language(language: str, detected_language: Optional[str]) -> str:
    if language == "auto-detect":
        if detected_language:
            st.markdown(f"{icon(Icons.INFO, '1em', '#58a6ff')} Auto-detected: **{detected_language}**", unsafe_allow_html=True)
            return detected_language
        else:
            st.markdown(f"{icon(Icons.WARNING, '1em', '#f59e0b')} Could not auto-detect. Defaulting to Python.", unsafe_allow_html=True)
            return "python"
    return language


def render_review_tabs(code_input: str, api_key: str, language: str, context: str, model: str, max_tokens: int, temperature: float, detected_language: Optional[str]) -> None:
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; color: var(--text-primary);">
            <i class="fas fa-bullseye" style="color: var(--accent-primary); font-size: 1.5em;"></i>
            Review Mode
        </h2>
        <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
            Select a review type below to analyze your code
        </p>
    </div>
    """, unsafe_allow_html=True)

    final_language = _resolve_language(language, detected_language)

    # Mode selector with persistence
    modes = [ReviewMode.DESIGN_FLAWS, ReviewMode.TEST_GENERATION, ReviewMode.REFACTORING, ReviewMode.SECURITY_REVIEW, ReviewMode.FULL_REVIEW]
    mode_icons = {
        ReviewMode.DESIGN_FLAWS: ("search", "#58a6ff"),
        ReviewMode.TEST_GENERATION: ("flask", "#7ee787"),
        ReviewMode.REFACTORING: ("code-branch", "#a371f7"),
        ReviewMode.SECURITY_REVIEW: ("shield-halved", "#f59e0b"),
        ReviewMode.FULL_REVIEW: ("robot", "#58a6ff")
    }
    mode_short_names = {
        ReviewMode.DESIGN_FLAWS: "Design Flaws",
        ReviewMode.TEST_GENERATION: "Generate Tests",
        ReviewMode.REFACTORING: "Refactoring",
        ReviewMode.SECURITY_REVIEW: "Security Audit",
        ReviewMode.FULL_REVIEW: "Full Review"
    }

    # Get saved mode
    saved_mode = st.session_state.get("analysis_mode", "FULL_REVIEW")
    mode_names = [m.name for m in modes]
    default_idx = mode_names.index(saved_mode) if saved_mode in mode_names else 4
    selected_mode = modes[default_idx]

    st.markdown("""<style>
    .review-mode-card {
        background: var(--bg-card);
        border: 1px solid var(--border-primary);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all var(--transition-normal);
    }

    .review-mode-card:hover {
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-md);
    }

    .cost-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: var(--radius-md);
        padding: 0.5rem 1rem;
        color: var(--accent-secondary);
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0.75rem 0;
    }

    .mode-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }

    .mode-description {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""
    <style>
    /* Enhanced mode dropdown styling */
    .mode-select-container {
        margin-bottom: 1rem;
    }

    .mode-select-container .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 2px solid var(--border-primary) !important;
        border-radius: var(--radius-lg) !important;
        padding: 0.25rem !important;
        transition: all 0.25s ease !important;
    }

    .mode-select-container .stSelectbox > div > div:hover {
        border-color: var(--accent-primary) !important;
        box-shadow: var(--shadow-md) !important;
    }

    .mode-select-container .stSelectbox > div > div:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15), var(--shadow-md) !important;
    }

    /* Dropdown option styling */
    .mode-select-container .stSelectbox [data-baseweb="select"] > div {
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Mode options with emojis for dropdown
    mode_options = {
        "🔍 Design Flaws — Detect SOLID violations and code smells": ReviewMode.DESIGN_FLAWS,
        "🧪 Generate Tests — Create comprehensive unit tests": ReviewMode.TEST_GENERATION,
        "♻️ Refactoring — Suggest clean code transformations": ReviewMode.REFACTORING,
        "🔒 Security Audit — OWASP Top 10 vulnerability analysis": ReviewMode.SECURITY_REVIEW,
        "🤖 Full Review — Comprehensive analysis covering all aspects": ReviewMode.FULL_REVIEW
    }

    # Reverse mapping for default selection
    mode_to_option = {v: k for k, v in mode_options.items()}
    default_option = mode_to_option.get(selected_mode, list(mode_options.keys())[4])

    st.markdown('<div class="mode-select-container">', unsafe_allow_html=True)
    selected_option = st.selectbox(
        "Select Review Mode",
        options=list(mode_options.keys()),
        index=list(mode_options.keys()).index(default_option),
        key="mode_selector",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    selected_mode = mode_options[selected_option]

    if selected_mode.name != st.session_state.get("analysis_mode", "FULL_REVIEW"):
        st.session_state.analysis_mode = selected_mode.name
        storage.save_analysis_mode(selected_mode.name)

    st.markdown(f"""
    <div class="review-mode-card">
        <div class="mode-header">
            <h3 style="margin: 0; color: var(--text-primary); font-size: 1.25rem; font-weight: 700;">
                {selected_mode.value}
            </h3>
        </div>
        <p class="mode-description">{_get_mode_description(selected_mode)}</p>
    </div>
    """, unsafe_allow_html=True)

    if code_input and code_input.strip():
        cost_estimate = estimate_cost(len(code_input), model, max_tokens)
        st.markdown(f"""
        <div class="cost-badge">
            <i class="fas fa-dollar-sign" style="font-size: 0.9em;"></i>
            <span>Est. cost: <strong>${cost_estimate['cost']:.4f}</strong></span>
            <span style="opacity: 0.7; font-size: 0.85em;">
                (~{cost_estimate['input_tokens']:,} in + ~{cost_estimate['output_tokens']:,} out)
            </span>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Analyze", key=f"btn_{selected_mode.name}", type="primary", use_container_width=True):
        is_valid_key, key_error = validate_api_key(api_key)
        if not is_valid_key:
            st.error(key_error)
        else:
            is_valid_code, code_error = validate_code_input(code_input)
            if not is_valid_code:
                st.error(code_error)
            else:
                _execute_analysis(api_key, code_input, final_language, selected_mode, context, model, max_tokens, temperature)

    _render_mode_result(selected_mode)


def render_project_review(project_files: Dict[str, str], api_key: str, context: str, model: str, max_tokens: int, temperature: float) -> None:
    st.markdown(f"### {icon('bullseye', '1em')} Project Analysis", unsafe_allow_html=True)

    if not project_files:
        st.markdown(f"{icon(Icons.INFO, '1em', '#58a6ff')} Upload project files on the left to begin analysis.", unsafe_allow_html=True)
        return

    st.markdown(f"**{ReviewMode.PROJECT_REVIEW.value}**")
    st.caption(_get_mode_description(ReviewMode.PROJECT_REVIEW))

    formatted_content = format_project_for_review(project_files)
    cost_estimate = estimate_cost(len(formatted_content), model, max_tokens)
    st.markdown(f"{icon(Icons.DOLLAR, '1em', '#10b981')} Est. cost: **${cost_estimate['cost']:.4f}** (~{cost_estimate['input_tokens']:,} in + ~{cost_estimate['output_tokens']:,} out)", unsafe_allow_html=True)

    if st.button("Analyze Project", key="btn_PROJECT_REVIEW", type="primary", use_container_width=True):
        is_valid_key, key_error = validate_api_key(api_key)
        if not is_valid_key:
            st.error(key_error)
        else:
            _execute_analysis(api_key, formatted_content, "multi-language", ReviewMode.PROJECT_REVIEW, context, model, max_tokens, temperature)

    _render_mode_result(ReviewMode.PROJECT_REVIEW)


def render_footer() -> None:
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Languages Supported", "15+")
    with col2:
        st.metric("Review Modes", "6")
    with col3:
        st.metric("Response Time", "~5 sec")
    with col4:
        st.metric("Session Analyses", len(st.session_state.get("history", [])))


def main() -> None:
    init_session_state()
    render_header()
    api_key, language, context, model, max_tokens, temperature = render_sidebar()

    # Mode switcher with styled tabs
    st.markdown("""<style>
    div[data-testid="stHorizontalBlock"] > div:first-child .stRadio > div {
        flex-direction: row; gap: 0; flex-wrap: wrap;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child .stRadio label {
        background: #161b22; border: 1px solid #30363d; padding: 0.5rem 1.5rem;
        margin: 0; cursor: pointer; transition: all 0.2s; white-space: nowrap;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child .stRadio label:first-of-type { border-radius: 8px 0 0 8px; }
    div[data-testid="stHorizontalBlock"] > div:first-child .stRadio label:last-of-type { border-radius: 0 8px 8px 0; }
    div[data-testid="stHorizontalBlock"] > div:first-child .stRadio label[data-checked="true"] {
        background: #58a6ff; border-color: #58a6ff; color: #0a0e14; font-weight: 600;
    }
    @media (max-width: 600px) {
        div[data-testid="stHorizontalBlock"] > div:first-child .stRadio > div { flex-direction: column; gap: 0.5rem; }
        div[data-testid="stHorizontalBlock"] > div:first-child .stRadio label { border-radius: 8px !important; }
    }
    </style>""", unsafe_allow_html=True)

    # Use plain text for radio (Streamlit doesn't support HTML in radio options)
    # Determine default index based on saved preference
    saved_mode = st.session_state.get("review_mode", "file")
    default_index = 1 if saved_mode == "project" else 0

    review_mode = st.radio(
        "Review Type",
        ["📄 File Review", "📁 Project Review"],
        horizontal=True,
        label_visibility="collapsed",
        key="review_type_selector",
        index=default_index
    )

    # Save review mode preference when changed
    current_mode = "project" if "Project" in review_mode else "file"
    if current_mode != st.session_state.get("review_mode", "file"):
        st.session_state.review_mode = current_mode
        storage.save_review_mode(current_mode)
    
    # Inject Font Awesome icons via CSS
    st.markdown("""
    <style>
    /* File Review icon - file-code */
    div[data-testid="stHorizontalBlock"] .stRadio label:first-of-type::before {
        font-family: "Font Awesome 6 Free";
        content: "\\f1c9";
        font-weight: 900;
        margin-right: 6px;
        display: inline-block;
    }
    /* Project Review icon - folder-open */
    div[data-testid="stHorizontalBlock"] .stRadio label:last-of-type::before {
        font-family: "Font Awesome 6 Free";
        content: "\\f07c";
        font-weight: 900;
        margin-right: 6px;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

    is_project_mode = "Project" in review_mode

    col1, col2 = st.columns([1, 1], gap="large")

    if is_project_mode:
        with col1:
            project_files, _ = render_project_input()
            st.divider()
            render_history()
        with col2:
            render_project_review(project_files, api_key, context, model, max_tokens, temperature)
    else:
        with col1:
            code_input, detected_language = render_code_input()
            st.divider()
            render_history()
        with col2:
            render_review_tabs(code_input, api_key, language, context, model, max_tokens, temperature, detected_language)

    render_footer()


if __name__ == "__main__":
    main()
