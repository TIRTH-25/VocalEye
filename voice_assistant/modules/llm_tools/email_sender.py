import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
from config.settings import GEMINI_API_KEY,SENDER_EMAIL,SENDER_PASSWORD
from modules.text_to_speech import speak

def _ensure_genai():
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key missing. Configure it in the installer or run the app's configuration.")
    genai.configure(api_key=GEMINI_API_KEY)

def generate_email_content(receiver_email,subject, topic):
    """Use Gemini to generate email content for the given topic."""
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
	You are an expert email writer. Write a professional, clear, and concise email. 
	
	Requirements:
	- Subject: {subject}
	- Recipient: {receiver_email}
    - Sender: {SENDER_EMAIL}
	- Tone: Formal but friendly
	- Length: 2–3 short paragraphs
	- Include a proper greeting(extract name from {receiver_email}) and closing(extract name from {SENDER_EMAIL})
	- Ensure the email is easy to understand and valuable for the recipient 

	Topic/Context: {topic}

	Return only the email body (without metadata).
	"""

    response = model.generate_content(prompt)
    return response.text.strip()

def send_email(receiver_email, subject, topic):
    _ensure_genai()
    """Generate an email using Gemini and send it via SMTP."""
    try:
        # Generate email body from Gemini
        temp=receiver_email.replace(" ","")
        receiver_email=temp
        email_body = generate_email_content(receiver_email,subject, topic)

        # Create MIME message
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(email_body, "plain"))

        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()

        speak("Email sent successfully!")
        return "Email sent successfully!"
    except Exception as e:
        speak("Error sending email")
        return "Error sending email"