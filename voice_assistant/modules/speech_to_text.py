import speech_recognition as sr
from modules.text_to_speech import speak

class SpeechToText:
    def __init__(self, energy_threshold=300, pause_threshold=0.8):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        # Set thresholds for smoother listening
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold

    def listen(self):
        """Continuously listen until user stops speaking."""
        with self.microphone as source:
            speak("Listening")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=None)
                
                text = self.recognizer.recognize_google(audio, language="en-IN")
                return text.strip()
            except OSError as e:
                speak("Microphone error! Please check your audio device.")
                return "Microphone error! Please check your audio device."

            except AssertionError as e:
                speak("Microphone initialization failed.")
                return "Microphone initialization failed."
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                speak("CHECK INTERNET CONNECTION PLEASE!!!")
                return "CHECK INTERNET CONNECTION PLEASE!!!"