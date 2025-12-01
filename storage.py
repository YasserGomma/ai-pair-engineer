"""Persistent storage for session data using JSON file."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

STORAGE_DIR = Path(".data")
HISTORY_FILE = STORAGE_DIR / "history.json"
RESULTS_FILE = STORAGE_DIR / "results.json"
SETTINGS_FILE = STORAGE_DIR / "settings.json"
MAX_HISTORY_ITEMS = 50


def _ensure_storage_dir() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)


def _load_json(filepath: Path) -> Dict:
    try:
        if filepath.exists():
            with open(filepath, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _save_json(filepath: Path, data: Dict) -> None:
    _ensure_storage_dir()
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except IOError:
        pass


def load_history() -> List[Dict]:
    data = _load_json(HISTORY_FILE)
    return data.get("history", [])


def save_history(history: List[Dict]) -> None:
    history = history[:MAX_HISTORY_ITEMS]
    _save_json(HISTORY_FILE, {"history": history, "updated_at": datetime.now().isoformat()})


def add_history_entry(entry: Dict) -> List[Dict]:
    history = load_history()
    history.insert(0, entry)
    history = history[:MAX_HISTORY_ITEMS]
    save_history(history)
    return history


def clear_history() -> None:
    _save_json(HISTORY_FILE, {"history": [], "updated_at": datetime.now().isoformat()})


def load_results() -> Dict[str, str]:
    data = _load_json(RESULTS_FILE)
    return data.get("results", {})


def save_result(mode_name: str, result: str) -> None:
    data = _load_json(RESULTS_FILE)
    if "results" not in data:
        data["results"] = {}
    data["results"][mode_name] = result
    data["updated_at"] = datetime.now().isoformat()
    _save_json(RESULTS_FILE, data)


def get_result(mode_name: str) -> Optional[str]:
    results = load_results()
    return results.get(mode_name)


def clear_result(mode_name: str) -> None:
    data = _load_json(RESULTS_FILE)
    if "results" in data and mode_name in data["results"]:
        del data["results"][mode_name]
        data["updated_at"] = datetime.now().isoformat()
        _save_json(RESULTS_FILE, data)


def clear_all_results() -> None:
    _save_json(RESULTS_FILE, {"results": {}, "updated_at": datetime.now().isoformat()})


def load_settings() -> Dict:
    return _load_json(SETTINGS_FILE)


def save_settings(settings: Dict) -> None:
    settings["updated_at"] = datetime.now().isoformat()
    _save_json(SETTINGS_FILE, settings)


def get_tokens() -> Dict[str, int]:
    settings = load_settings()
    return settings.get("tokens", {"input": 0, "output": 0})


def add_tokens(input_tokens: int, output_tokens: int) -> None:
    settings = load_settings()
    if "tokens" not in settings:
        settings["tokens"] = {"input": 0, "output": 0}
    settings["tokens"]["input"] += input_tokens
    settings["tokens"]["output"] += output_tokens
    save_settings(settings)


def get_cost() -> float:
    settings = load_settings()
    return settings.get("total_cost", 0.0)


def get_code_input() -> str:
    settings = load_settings()
    return settings.get("code_input", "")


def save_code_input(code: str) -> None:
    settings = load_settings()
    settings["code_input"] = code
    save_settings(settings)


def get_review_mode() -> str:
    settings = load_settings()
    return settings.get("review_mode", "file")


def save_review_mode(mode: str) -> None:
    settings = load_settings()
    settings["review_mode"] = mode
    save_settings(settings)


def get_analysis_mode() -> str:
    settings = load_settings()
    return settings.get("analysis_mode", "FULL_REVIEW")


def save_analysis_mode(mode: str) -> None:
    settings = load_settings()
    settings["analysis_mode"] = mode
    save_settings(settings)


def add_cost(cost: float) -> None:
    settings = load_settings()
    settings["total_cost"] = settings.get("total_cost", 0.0) + cost
    save_settings(settings)


def reset_cost_tracker() -> None:
    settings = load_settings()
    settings["tokens"] = {"input": 0, "output": 0}
    settings["total_cost"] = 0.0
    save_settings(settings)
