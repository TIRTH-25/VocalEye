
import tkinter as tk
from tkinter import messagebox
import keyring
from config.settings import SERVICE_NAME

    # ---------------- VALIDATION HELPERS ---------------- #
def validate_email(email):
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))

def validate_gemini_key(key):
    return key.startswith("AIza") and 35 <= len(key) <= 45

def validate_app_password(pwd):
    return len(pwd) == 16 and pwd.isalnum()

def run_config_ui(on_close=None):
    def save_and_close():
        gem = gem_entry.get().strip()
        email = email_entry.get().strip()
        pwd = pass_entry.get().strip()
        if not all([gem, email, pwd]):
            messagebox.showerror("Missing", "Please fill all fields.")
            return
        if not validate_gemini_key(gem):
                messagebox.showerror("Invalid Gemini API Key", "Key must start with 'AIza' and be 35–45 chars.")
                return
        if not validate_email(email):
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
                return
        if not validate_app_password(pwd):
                messagebox.showerror("Invalid App Password", "Must be exactly 16 characters (letters/numbers).")
                return
        try:
            keyring.set_password(SERVICE_NAME, "GEMINI_API_KEY", gem)
            keyring.set_password(SERVICE_NAME, "SENDER_EMAIL", email)
            keyring.set_password(SERVICE_NAME, "SENDER_PASSWORD", pwd)
            messagebox.showinfo("Saved", "Credentials saved successfully.")
            root.destroy()
            if on_close:
                on_close()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    root = tk.Tk()
    root.title("VocalEye Configuration")
    root.geometry("420x220")
    tk.Label(root, text="Gemini API Key:").pack()
    gem_entry = tk.Entry(root, width=60)
    gem_entry.pack()
    tk.Label(root, text="Sender Email:").pack()
    email_entry = tk.Entry(root, width=60)
    email_entry.pack()
    tk.Label(root, text="App Password:").pack()
    pass_entry = tk.Entry(root, width=60, show="*")
    pass_entry.pack(pady=5)
    tk.Button(root, text="Save", command=save_and_close).pack(pady=8)
    root.mainloop()