import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "whisper_model": "base",
    "audio_device_index": None,
    "audio_source_type": "mic",
    "silence_threshold": 0.01,
    "silence_duration": 1.2,
    "compute_type": "int8",
    "gemini_model": "gemini-3.1-flash-lite",
    "noise_reduction_enabled": True,
    "history": []
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Update default config to handle potential missing keys
                    for k, v in loaded.items():
                        self.config[k] = v
            except Exception as e:
                print(f"Error loading config: {e}")
                self.config = DEFAULT_CONFIG.copy()
        else:
            # Check environment variable before creating default config
            env_key = os.environ.get("GEMINI_API_KEY", "")
            if env_key:
                self.config["gemini_api_key"] = env_key
            self.save()
            
        # Fallback to env var if key is empty (e.g. cloned repo setup)
        if not self.config.get("gemini_api_key"):
            env_key = os.environ.get("GEMINI_API_KEY", "")
            if env_key:
                self.config["gemini_api_key"] = env_key

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def add_to_history(self, question, analysis_result):
        # Keeps session history, max 20 items
        history = self.config.get("history", [])
        # Avoid duplicate consecutive questions
        if history and history[0].get("question") == question:
            return
        
        history.insert(0, {
            "question": question,
            "analysis": analysis_result
        })
        self.config["history"] = history[:20]
        self.save()

    def clear_history(self):
        self.config["history"] = []
        self.save()
