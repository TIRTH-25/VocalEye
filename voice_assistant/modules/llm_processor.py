import google.generativeai as genai
from config.settings import GEMINI_API_KEY
from modules.llm_tools.generate_os_command import generate_os_command
from modules.llm_tools.create_file import file_generator
from modules.llm_tools.email_sender import send_email
from google.generativeai.types import FunctionDeclaration, Tool
from modules.llm_tools.code_builder import build_project_from_text


# -------------------------------
# Configure Gemini API
# -------------------------------
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------------
# Define tools
# -------------------------------
tasks = [
    {
        "name": "file_generator",
        "description": "Generate content about a topic and create pdf, docx, or pptx file.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "filetype": {"type": "string", "enum": ["txt", "pdf", "docx", "pptx"]},
                "save_path": {"type": "string"}
            },
            "required": ["topic", "filetype"]
        }
    },
    {
        "name": "generate_os_command",
        "description": ("execute all type of desktop task given by you"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_text": {
                    "type": "string",
                    "description": (
                        "Natural language instruction from the user that related to do any desktop task"
                    )
                }
            },
            "required": ["user_text"]
        }
    },

    {
        "name": "send_email",
        "description": "Send an email to any email id.",
        "parameters": {
            "type": "object",
            "properties": {
                "receiver_email": {"type": "string"},
                "subject": {"type": "string"},
                "topic": {"type": "string"}
            },
            "required": ["receiver_email", "subject", "topic"]
        }
    },

    {
        "name": "code_builder",
        "description": "From a natural-language description, produce a production-ready project skeleton, files, and optionally run the project.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_text": {"type": "string"},
                "base_path": {"type": "string"},
                "run_command_override": {"type": "string"}
            },
            "required": ["user_text"]
        }
    },

]

# Convert tasks → Gemini-compatible tool declarations
function_declarations = [
    FunctionDeclaration(
        name=t["name"], description=t["description"], parameters=t["parameters"]
    )
    for t in tasks
]

tools = [Tool(function_declarations=function_declarations)]

# -------------------------------
# Tool handler functions
# -------------------------------
def handle_tool_call(name, args):
    if name == "generate_os_command":
        return generate_os_command(args["user_text"])
    elif name == "file_generator":
        return file_generator(args["topic"], args.get("filetype", "txt"), args.get("save_path"))
    elif name == "send_email":
        return send_email(args["receiver_email"], args.get("subject", "none"), args.get("topic"))
    elif name == "code_builder":
        return build_project_from_text(
            args["user_text"],
            base_path=args.get("base_path"),
            run_command_override=args.get("run_command_override")
        )

    return "Tool not implemented"


# -------------------------------
# Model setup (chat mode)
# -------------------------------
model = genai.GenerativeModel("gemini-2.0-flash", tools=tools)

# Persistent chat session — keeps context automatically
chat = model.start_chat(history=[])


# -------------------------------
# Core processing function
# -------------------------------
def process_with_llm(user_input):
    """
    Main LLM interface.
    - Decides when to use tools vs reply normally.
    - Maintains conversation history automatically.
    - Returns result text for speaking/display.
    """
    try:
        response = chat.send_message(
            f"You are a voice-based AI assistant with access to tools.\n"
            f"Use tools ONLY if the user asks to perform an action "
            f"(e.g., create file, open browser, send email).\n"
            f"For questions, replies, or casual chat, respond normally.\n\n"
            f"User: {user_input}"
        )

        results = []

        if hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts
            used_tool = False

            for part in parts:
                if hasattr(part, "function_call") and part.function_call:
                    used_tool = True
                    call = part.function_call
                    name = call.name
                    args = call.args
                    result = handle_tool_call(name, args)
                    results.append(f"{name} → {result}")

            if not used_tool:
                if hasattr(response, "text") and response.text:
                    results.append(response.text)
                else:
                    results.append("I'm not sure how to respond.")
        else:
            results.append(response.text or "I'm not sure how to respond.")

        return "\n\n".join(results)

    except Exception as e:
        return f"An error occurred {e}"