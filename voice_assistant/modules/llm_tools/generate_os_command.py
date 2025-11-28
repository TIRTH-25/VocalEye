import google.generativeai as genai
from config.settings import GEMINI_API_KEY, CURRENT_OS
from modules.command_executor import execute_command
from modules.text_to_speech import speak
import os
import platform
import subprocess

def _ensure_genai():
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key missing. Configure it in the installer or run the app's configuration.")
    genai.configure(api_key=GEMINI_API_KEY)

# ------------------ WINDOWS ------------------
def get_windows_start_menu_apps():
    """Get apps from Start Menu (.lnk shortcuts)."""
    start_menu_paths = [
        os.path.join(os.environ.get("ProgramData", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
    ]
    apps = []
    for path in start_menu_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        apps.append(os.path.splitext(file)[0])
    return apps

def get_windows_uwp_apps():
    """Get Microsoft Store (UWP) apps using PowerShell."""
    try:
        cmd = ["powershell", "-Command", "Get-StartApps | Select-Object -Property Name"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return [line.strip() for line in result.stdout.splitlines()
                if line.strip() and "Name" not in line]
    except Exception as e:
        return [f"Error fetching UWP apps: {e}"]

def get_windows_apps():
    apps = set()
    apps.update(get_windows_start_menu_apps())
    apps.update(get_windows_uwp_apps())
    return sorted(apps)

# ------------------ LINUX ------------------
def get_linux_apps():
    """Get apps from .desktop files in system/user directories."""
    desktop_dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications")
    ]
    apps = []
    for path in desktop_dirs:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(".desktop"):
                    apps.append(os.path.splitext(file)[0])
    return sorted(set(apps))

# ------------------ MACOS ------------------
def get_macos_apps():
    """Get apps from Applications folders."""
    app_dirs = [
        "/Applications",
        "/System/Applications",
        os.path.expanduser("~/Applications")
    ]
    apps = []
    for path in app_dirs:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(".app"):
                    apps.append(os.path.splitext(file)[0])
    return sorted(set(apps))

# ------------------ MAIN ------------------
def get_all_apps():
    system = platform.system()
    if system == "Windows":
        return get_windows_apps()
    elif system == "Linux":
        return get_linux_apps()
    elif system == "Darwin":  # macOS
        return get_macos_apps()
    else:
        return [f"Unsupported OS: {system}"]

apps = get_all_apps()


def generate_os_command(user_text):
    _ensure_genai()
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    You are an AI that converts natural language into exact {platform.system().lower() } terminal commands.

    Rules:
    1. Always output ONLY the exact command — no explanations, no extra text.
    2. If the user asks to open a program (e.g., Chrome) but no URL is provided,
    default to opening the homepage https://google.com.
    3. For Windows:
    - Use 'start' for opening applications, e.g., start chrome "https://google.com"
    4. For Linux:
    - Use 'xdg-open' for URLs, e.g., xdg-open "https://google.com"
    5. For macOS:
    - Use 'open' for URLs, e.g., open "https://google.com"
    6. If the request is unclear, make your best guess for a safe default.
     7.if the application for which we have to generate os command is present in {apps} then treat that is desktop application and give commands according to that otherwise give commands to operate that application in browser.

    Request: "{user_text}"
    """


    response = model.generate_content(prompt)
    command = response.text.strip()
    
    if command:
        result = execute_command(command)
        speak(result)
    else:
        speak("I could not generate a command for that request.")
    return command
