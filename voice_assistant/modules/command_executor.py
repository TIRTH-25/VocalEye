import subprocess
import platform
import shlex

def execute_command(command: str):
    try:
        system = platform.system()

        # ---------------------------
        # Windows
        # ---------------------------
        if system == "Windows":
            # Use PowerShell for better compatibility
            completed = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True
            )

        # ---------------------------
        # Linux & macOS
        # ---------------------------
        else:
            completed = subprocess.run(
                command,
                shell=True,           # shell=True is safe for controlled commands
                capture_output=True,
                text=True
            )

        # If command failed OR return code not 0
        if completed.returncode != 0:
            return "Execution Failed"

        return completed.stdout.strip() or "Command executed successfully."

    except Exception as e:
        return "Execution Failed"


