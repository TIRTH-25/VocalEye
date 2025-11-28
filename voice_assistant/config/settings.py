# config/settings.py
import os
import platform
import configparser
from pathlib import Path

CURRENT_OS = platform.system().lower()
DEFAULT_SAVE_PATH = Path.home() / "Documents" / "AssistantOutputs"
DEFAULT_SAVE_PATH.mkdir(parents=True, exist_ok=True)
SERVICE_NAME = "VocalEye"

def _get_secret(name: str):
    v = os.getenv(name)
    if v:
        return v

    try:
        import keyring
        v = keyring.get_password(SERVICE_NAME, name)
        if v:
            return v
    except Exception:
        pass

    cfg_path = Path(__file__).resolve().parent / "config.ini"
    if cfg_path.exists():
        cp = configparser.ConfigParser()
        cp.read(cfg_path)
        if cp.has_section("credentials") and cp.has_option("credentials", name):
            value = cp.get("credentials", name)
            try:
                import keyring
                keyring.set_password(SERVICE_NAME, name, value)
            except Exception:
                pass
            try:
                cfg_path.unlink()
            except Exception:
                pass
            return value
    return None

GEMINI_API_KEY = _get_secret("GEMINI_API_KEY")
SENDER_EMAIL = _get_secret("SENDER_EMAIL")
SENDER_PASSWORD = _get_secret("SENDER_PASSWORD")

CONFIGURED = all([GEMINI_API_KEY, SENDER_EMAIL, SENDER_PASSWORD])
