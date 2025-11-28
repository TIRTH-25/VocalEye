import pyttsx3


def speak(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)  # speaking speed
    engine.setProperty("volume", 1)  # max volume
    
    engine.say(text)
    engine.runAndWait()