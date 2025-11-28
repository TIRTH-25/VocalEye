import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
from config.settings import GEMINI_API_KEY,SENDER_EMAIL,SENDER_PASSWORD

# 🔑 Configure your Gemini API Key
genai.configure(api_key=GEMINI_API_KEY)

def generate_email_content(receiver_email,subject, topic):
    """Use Gemini to generate email content for the given topic."""
    model = genai.GenerativeModel("gemini-2.0-flash")
    prompt = f"""
	You are an expert email writer. Write a professional, clear, and concise email. 
	
	Requirements:
	- Subject: {subject}
	- Recipient: {receiver_email}
	- Tone: Formal but friendly
	- Length: 2–3 short paragraphs
	- Include a proper greeting and closing
	- Ensure the email is easy to understand and valuable for the recipient

	Topic/Context: {topic}

	Return only the email body (without metadata).
	"""

    response = model.generate_content(prompt)
    return response.text.strip()

def send_email(receiver_email, subject, topic):
    """Generate an email using Gemini and send it via SMTP."""
    try:
        # Generate email body from Gemini
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

        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"⚠️ Error sending email: {e}")
        return False



if __name__ == "__main__":
    receiver_email = "jainilmochi12@gmail.com"
    subject = "Project Update"
    topic = "Update about the VocalEye project progress for our minor submission."

    send_email(receiver_email, subject, topic)







