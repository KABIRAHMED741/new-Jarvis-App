

 # new======>

import pyttsx3
import speech_recognition as sr
import eel
import time


def speak(text):
    text = str(text)
# # Initialize TTS engine only once (optimization)
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 174)
    """Speak out the given text and show it in UI."""
    eel.DisplayMessage(text)
    engine.say(text)
    eel.receiverText(text)
    engine.runAndWait()



# @eel.expose
def takecommand():
    """Listen to user voice input and return recognized text."""
    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        eel.DisplayMessage("Listening...")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)

        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=6)
        except Exception as e:
            print(f"Listening error: {e}")
            return ""

    try:
        print("Recognizing...")
        eel.DisplayMessage("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"User said: {query}")
        eel.DisplayMessage(query)
        time.sleep(2)
        return query.lower()
    except Exception as e:
        print(f"Recognition error: {e}")
        return ""
   

@eel.expose
def allCommands(message=1):
    if message==1:
       query = takecommand()
       print(query) 
       eel.senderText(query) 
    else:
        query= message  
        eel.senderText(query)      
    """Route user commands to correct feature functions."""
    try:
       
        if not query:
            return  # nothing said
      
        print(f"Command received: {query}")

        if "open" in query:
            from engine.features import openCommand
            openCommand(query)

        elif "on youtube" in query:
            from engine.features import PlayYoutube
            PlayYoutube(query)

        elif ("message" in query and "send" in query) or \
            ("make a call" in query) or \
            ("phone call" in query) or \
            ("video call" in query) or \
            (query.startswith("call ")):
            
            from engine.features import findContact, whatsApp
            contact_no, name = findContact(query)

            if contact_no != 0:
                if "message" in query:
                    speak("What message should I send?")
                    msg = takecommand()
                    flag = "message"

                elif "video call" in query:
                    msg, flag = "", "video call"

                else:  # covers "make a call", "phone call", "call <name>"
                    msg, flag = "", "call"

                whatsApp(contact_no, msg, flag, name)             
     
        else: # If no matching command, send to chatbot 
            from engine.features import chatBot 
            chatBot(query)

    except Exception as e:
        print(f"Error in allCommands: {e}")
   
    eel.ShowHood()
 