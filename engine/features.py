

# new
import os
import sqlite3
import struct
import subprocess
import threading
import time
import pyautogui
import webbrowser
from shlex import quote
from playsound import playsound
import eel
import pvporcupine
import pyaudio

# nn+
try:
    import pywhatkit as kit
except Exception as e:
    print(f"⚠️ pywhatkit not available: {e}")
    kit = None
# nn+


from engine.command import speak 
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term, remove_words

# Database connection
con = sqlite3.connect("jarvis.db", check_same_thread=False)
cursor = con.cursor()


@eel.expose
def playAssistantSound():
    """Play start sound when assistant wakes up."""
    music_dir = "www\\assets\\audio\\start_sound.mp3"

    playsound(music_dir)


def openCommand(query: str):
    """Open applications or websites from DB or system."""

    from engine.command import speak #new line

    query = query.replace(ASSISTANT_NAME, "").replace("open", "").strip().lower()
    app_name = query

    if not app_name:
        return

    try:
        # Check system commands
        cursor.execute("SELECT path FROM sys_command WHERE name=?", (app_name,))
        results = cursor.fetchall()

        if results:
            speak(f"Opening {app_name}")
            os.startfile(results[0][0])
            return

        # Check web commands
        cursor.execute("SELECT url FROM web_command WHERE name=?", (app_name,))
        results = cursor.fetchall()

        if results:
            speak(f"Opening {app_name}")
            webbrowser.open(results[0][0])
            return

        # Fallback to OS
        speak(f"Opening {app_name}")
        os.system(f"start {app_name}")

    except Exception as e:
        speak("Something went wrong")
        print(f"openCommand error: {e}")
       


def PlayYoutube(query: str):
    """Play searched term on YouTube."""
    search_term = extract_yt_term(query)
    speak(f"Playing {search_term} on YouTube")
    kit.playonyt(search_term)




# ---------------- HOTWORD DETECTION ----------------
def hotword(queue=None):
    """Listen continuously for wake word (Jarvis/Alexa)."""
    porcupine, paud, audio_stream = None, None, None
    try:
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
        )

        print("Listening For Hotword..🎙️")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Hotword detected..🔥")
                threading.Thread(target=trigger_action, daemon=True).start()

    except KeyboardInterrupt:
        print("Stopped manually.")
    except Exception as e:
        print(f"Hotword error: {e}")
    finally:
        if porcupine:
            porcupine.delete()
        if audio_stream:
            audio_stream.close()
        if paud:
            paud.terminate()


def trigger_action():
    """Triggered when hotword is detected (Jarvis/Alexa)."""
    try:
        pyautogui.hotkey("win", "j")  # Example action
        time.sleep(0.1)
    except Exception as e:
        print(f"Action error: {e}")


# ---------------- CONTACTS ----------------
def findContact(query: str):
    """Find contact number from DB using query."""

    words_to_remove = [
        ASSISTANT_NAME, "make", "a", "to", "phone", "call", "send",
        "message", "whatsapp", "video",
    ]
    query = remove_words(query, words_to_remove).strip().lower()

    try:
        cursor.execute(
            "SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?",
            ("%" + query + "%", query + "%"),
        )
        results = cursor.fetchall()

        if not results:
            speak("Contact not found")
            return 0, 0

        mobile_number_str = str(results[0][0])
        if not mobile_number_str.startswith("+91"):
            mobile_number_str = "+91" + mobile_number_str

        return mobile_number_str, query
    except Exception as e:
        speak("Error fetching contact")
        print(f"findContact error: {e}")
        return 0, 0
       
    

# ---------------- WHATSAPP ----------------
def whatsApp(mobile_no: str, message: str, flag: str, name: str):
    """Send WhatsApp message or make call."""

    from engine.command import speak  #newline

    if flag == "message":
        target_tab, jarvis_message = 12, f"Message sent successfully to {name}"
    elif flag == "call":
        target_tab, message, jarvis_message = 7, "", f"Calling {name}"
    else:
        target_tab, message, jarvis_message = 6, "", f"Starting video call with {name}"

    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
    full_command = f'start "" "{whatsapp_url}"'
    
    try:
        subprocess.run(full_command, shell=True)
        time.sleep(3)

        pyautogui.hotkey("ctrl", "f")
        for _ in range(1, target_tab):
            pyautogui.hotkey("tab")

        pyautogui.hotkey("enter")
        speak(jarvis_message)
    except Exception as e:
        speak("Error in WhatsApp function")  #undo 
        print(f"whatsApp error: {e}")  #undo

if __name__ == "__main__":
    hotword()

# Speech Function
# ------------------------

from engine.config import DEFAULT_MODEL

def chatBot(query):
    """
    Chatbot function using Ollama (replaces HuggingChat).
    """
    import requests
    try:
        import ollama
    except Exception:
        ollama = None 

    user_input = str(query).strip()
    text = ""

    # 1) Try with Ollama Python client if available
    if ollama is not None:
        try:
            response = ollama.chat(
                model=DEFAULT_MODEL,   # 👈 use the model you pulled
                messages=[{"role": "user", "content": user_input}]
            )
            try:
                text = response["message"]["content"]
            except Exception:
                text = str(response)
        except Exception as e:
            text = f"Error from Ollama client: {e}"

    # 2) Fallback to REST API if Python client fails
  
    # else: #undo
        try:
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [{"role": "user", "content": user_input}],
                "stream": False
            }
            r = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            if "message" in data and "content" in data["message"]:
                text = data["message"]["content"]
            elif "response" in data:
                text = data["response"]
            else:
                text = str(data)
        except Exception as e:
            text = f"Error connecting to Ollama server: {e}"



    print(" JARVIS reply:", text)
    #  Speak only if there's something to say
    if text and text.strip():
        try:
            speak(text)
            time.sleep(0.2)
        except Exception as e:
            print(f"⚠️ Speech error: {e}")
    else:
        print("⚠️ No text received to speak.")
    return text
 