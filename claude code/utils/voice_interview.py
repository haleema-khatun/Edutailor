import pyttsx3
import speech_recognition as sr

# Initialize text-to-speech
engine = pyttsx3.init()

engine.setProperty('rate', 160)
engine.setProperty('volume', 1)

def speak(text):
    print("AI:", text)
    engine.say(text)
    engine.runAndWait()


def listen():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)

        audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            print("You:", text)
            return text

        except:
            return "Sorry, I did not understand."