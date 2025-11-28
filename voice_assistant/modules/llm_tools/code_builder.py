# modules/llm_tools/code_builder.py
import os
import json
import shlex
import subprocess
import tempfile
from pathlib import Path
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, DEFAULT_SAVE_PATH
from modules.text_to_speech import speak




# ------------------ Gemini config helper ------------------
def _ensure_genai():
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key missing. Configure it in the installer or run the app's configuration.")
    genai.configure(api_key=GEMINI_API_KEY)
    

# ------------------ Safety helpers ------------------
FORBIDDEN_SUBSTRINGS = [
    "rm -rf /", "rm -rf --no-preserve-root /", "shutdown", "reboot", "mkfs", "dd if=",
    ">: /", "passwd", "chpasswd", "sudo", "reboot", "halt", "poweroff", "iptables", "ufw",
    "curl -s https://", "wget https://", "nc -l", "ncat", "python -c \"import os; os.system(",
]

def is_command_safe(cmd: str) -> bool:
    low = cmd.lower()
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in low:
            return False
    # also disallow absolute paths outside project
    if "/" in cmd and (" /" in cmd or cmd.strip().startswith("/")):
        # Allow relative paths; disallow naked absolute filesystem manipulation
        return False
    return True

# ------------------ Prompt template ------------------
MANIFEST_PROMPT = r"""
You are an elite Principal Software Architect and Multi-stack Engineering System.
Your job is to convert the user's request into a **complete production-grade application blueprint**
with advanced architecture, graphics, UI, backend, and automation.

Your output must be ONLY a JSON manifest (no explanation, no commentary):

{{
  "project_name": "<short>",
  "root": "",
  "architecture": "<full description of the system architecture>",
  "tech_stack": ["list", "of", "tech"],
  "files": [
    {{
      "path": "folder/file.ext",
      "content": "full production-ready code",
      "executable": false
    }}
  ],
  "run_command": "<safe run command>"
}}

==============================================================
                  GLOBAL SYSTEM REQUIREMENTS
==============================================================

⚡ Generate **real, production-quality**, fully functioning code.
⚡ NEVER generate placeholder code like “TODO”, “your code here”.
⚡ NEVER include explanations outside the JSON.

==============================================================
                  HIGH LEVEL COMPLEX APPLICATIONS
==============================================================

When user requests advanced or graphical applications, you MUST include:

### 1. High-Level Graphics & Rendering Support
Choose the best framework:
- WebGL / WebGPU
- Three.js / Babylon.js
- Canvas 2D / SVG
- PyGame / PyOpenGL
- Unity-like ECS architecture
- DirectX / Vulkan abstractions (if requested)
- Tkinter + PIL for desktop UI
- Processing.js / p5.js

Provide:
- Scene graphs
- Animation loops
- Asset loaders
- Input handlers (mouse, keyboard)
- Real UI with panels, overlays, HUD
- Event-driven architecture

### 2. Full Frontend Engineering
If web:
- React or Next.js 15+
- TailwindCSS or MUI
- Reusable components in `components/`
- Pages, routing
- Global state (Context, Zustand, Redux Toolkit)
- API services in `services/`
- Error boundaries
- Optimized rendering & lazy loading

### 3. Backend Engineering
Choose best option based on complexity:
- FastAPI (Python)
- Express/NestJS (Node)
- C# ASP.NET Core WebAPI
- Java Spring Boot

Include:
- controllers/
- services/
- repositories/
- models/
- database integration (MongoDB/Postgres/MySQL)
- JWT authentication
- Configurable env files
- Validation + schema enforcement
- Logging + error middleware

### 4. Enterprise Requirements (MANDATORY)
- `.gitignore`
- `README.md` with instructions
- `tests/` folder with at least one working real test
- `config/` folder
- `package.json` / `requirements.txt` written properly
- `.env.example` with environment variables
- Modular folder structure
- Clean architecture (domain / service / infra layers)

### 5. Graphics-Specific Requirements
If user wants:
- 3D → use Three.js or PyOpenGL
- Desktop app → use PyQt, Tkinter, or C# WPF
- Game → include:
  - game loop
  - input system
  - entity system
  - physics stub or engine integration
  - rendering engine
  - scene manager
- AI features → integrate Gemini API calls but NEVER include API keys

==============================================================
                   OUTPUT RULES (MANDATORY)
==============================================================

1. Output must be **pure JSON**.
2. Do not include comments inside JSON.
3. All file content must be real, complete code.
4. No partial code, no placeholders.

==============================================================
### USER REQUEST:
---
{user_text}
---
"""



# ------------------ Core functions ------------------
def request_manifest_from_gemini(user_text: str) -> dict:
    """Ask Gemini-2.0 to produce a JSON manifest describing the project files."""
    _ensure_genai()
    # Use the strict gemini-2.0 model (user requested)
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = MANIFEST_PROMPT.format(user_text=user_text.strip())
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Try to load JSON strictly.
    try:
        manifest = json.loads(text)
    except Exception as e:
        # If parsing failed, try to recover by scanning for the first { ... } block.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                manifest = json.loads(text[start:end+1])
            except Exception as e2:
                raise RuntimeError(f"Failed to parse JSON manifest from model response. Parse error: {e2}\nRaw response:\n{text}") from e2
        else:
            raise RuntimeError(f"Failed to parse JSON manifest from model response. Raw response:\n{text}") from e

    return manifest

def write_manifest_to_disk(manifest: dict, base_path: str = None) -> dict:
    """
    Writes files specified in manifest to disk.
    Returns dict with created file paths.
    """
    if base_path is None or base_path == "":
        base = Path(DEFAULT_SAVE_PATH) / (manifest.get("project_name") or "gem_project")
    else:
        base = Path(base_path).expanduser().resolve()

    # allow root override inside base directory
    root = manifest.get("root") or ""
    if root:
        base = base / root

    created = {"base": str(base), "files": []}
    os.makedirs(base, exist_ok=True)

    for f in manifest.get("files", []):
        relpath = f.get("path")
        if not relpath:
            continue
        file_path = base / relpath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = f.get("content", "")
        # write as text file (utf-8)
        with open(file_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        if f.get("executable"):
            try:
                file_path.chmod(file_path.stat().st_mode | 0o111)
            except Exception:
                pass
        created["files"].append(str(file_path))
    return created

def safe_run_command(run_command: str, cwd: str, timeout: int = 30) -> dict:
    """Executes a safe run command with automatic shell detection."""
    if not run_command:
        return {"skipped": True, "reason": "No run command provided."}

    if not is_command_safe(run_command):
        return {"skipped": True, "reason": "Run command considered unsafe."}

    # Windows requires shell=True for npm, dotnet, python, etc.
    use_shell = os.name == "nt"

    try:
        proc = subprocess.run(
            run_command if use_shell else shlex.split(run_command),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=use_shell
        )

        return {
            "skipped": False,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr
        }

    except subprocess.TimeoutExpired as te:
        return {"skipped": False, "timeout": True, "detail": str(te)}

    except FileNotFoundError as fnf:
        return {
            "skipped": False,
            "error": "command not found",
            "detail": str(fnf)
        }

    except Exception as e:
        return {"skipped": False, "error": str(e)}


# ------------------ Public API for integration ------------------
def build_project_from_text(user_text: str, base_path: str = None,
                            run_command_override: str = None, run_timeout: int = 3000):
    try:
        manifest = request_manifest_from_gemini(user_text)
    except Exception as e:
        speak("I could not generate the project structure.")
        return {"error": f"manifest_error: {e}"}

    if "files" not in manifest or not isinstance(manifest["files"], list):
        return {"error": 'Manifest missing "files" list'}

    try:
        created = write_manifest_to_disk(manifest, base_path)
    except Exception as e:
        speak("Disk write failed.")
        return {"error": f"disk_write_error: {e}"}

    # pick final run command
    final_cmd = run_command_override or manifest.get("run_command", "")

    exec_result = safe_run_command(final_cmd, created["base"], timeout=run_timeout)

    try:
        if exec_result.get("skipped"):
            speak("Project created. Execution skipped.")
        elif exec_result.get("returncode", 1) == 0:
            speak("Project created and executed successfully.")
        else:
            speak("Project created. Execution returned errors.")
    except:
        pass

    return {
        "manifest": manifest,
        "created": created,
        "execution": exec_result
    }

    