
from config import settings
from tools.app_ui import run_app_ui
from tools.first_run_config import run_config_ui

if __name__ == "__main__":
    if not settings.CONFIGURED:
        run_config_ui(on_close=run_app_ui)
    else:
        run_app_ui()