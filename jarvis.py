import whisper
import sounddevice
import numpy as np
import requests
import subprocess
import os
import webbrowser
import winsound
import keyboard
import threading
import pystray
import asyncio
import tempfile
import edge_tts
import pygame
from PIL import Image, ImageDraw

# ── CONFIGURAZIONE ──────────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "mistral:7b-instruct-q4_0"
LINGUA      = "it"
TASTO       = "F12"
DURATA_REC  = 4
VOCE        = "it-IT-DiegoNeural"   # voce italiana maschile AI

# ── APP CONFIGURATE ──────────────────────────────────────────────
APP = {
    "chrome":             "start chrome",
    "firefox":            "start firefox",
    "musica":            "start Apple Music:",
    "notepad":            "start notepad",
    "blocco note":        "start notepad",
    "explorer":           "start explorer",
    "file":               "start explorer",
    "word":               "start winword",
    "excel":              "start excel",
    "powerpoint":         "start powerpnt",
    "vlc":                "start vlc",
    "discord":            "start discord:",
    "telegram":           "start telegram",
    "whatsapp":           "start whatsapp",
    "calcolatrice":       "start calc",
    "task manager":       "start taskmgr",
    "impostazioni":       "start ms-settings:",
    "vscode":             "start code",
    "visual studio code": "start code",
    "visual studio":      "start code",
}

# ── SITI RAPIDI ──────────────────────────────────────────────────
SITI = {
    "youtube":    "https://www.youtube.com",
    "gmail":      "https://mail.google.com",
    "google":     "https://www.google.com",
    "facebook":   "https://www.facebook.com",
    "instagram":  "https://www.instagram.com",
    "twitter":    "https://www.twitter.com",
    "x":          "https://www.x.com",
    "netflix":    "https://www.netflix.com",
    "amazon":     "https://www.amazon.it",
    "wikipedia":  "https://www.wikipedia.org",
    "maps":       "https://maps.google.com",
    "drive":      "https://drive.google.com",
    "calendario": "https://calendar.google.com",
    "meet":       "https://meet.google.com",
    "chatgpt":    "https://chat.openai.com",
}

# ── SYSTEM PROMPT ────────────────────────────────────────────────
lista_app  = ", ".join(APP.keys())
lista_siti = ", ".join(SITI.keys())

SYSTEM_PROMPT = f'''Sei Jarvis, un assistente AI che controlla un PC Windows.
Rispondi SEMPRE e SOLO con uno di questi formati esatti, niente altro:

APRI:nome_app
CERCA:termine di ricerca
SITO:https://url-completo.com
RISPOSTA:testo della risposta
MULTISTEP:comando1|comando2|comando3

App disponibili: {lista_app}
Siti rapidi: {lista_siti}

Esempi corretti:
Utente: "apri chrome"                        → APRI:chrome
Utente: "apri spotify"                       → APRI:spotify
Utente: "cerca meteo domani"                 → CERCA:meteo domani
Utente: "vai su youtube"                     → SITO:https://www.youtube.com
Utente: "vai su gmail"                       → SITO:https://mail.google.com
Utente: "apri youtube e gmail"               → MULTISTEP:SITO:https://www.youtube.com|SITO:https://mail.google.com
Utente: "apri chrome e spotify"              → MULTISTEP:APRI:chrome|APRI:spotify
Utente: "cerca il meteo e apri youtube"      → MULTISTEP:CERCA:meteo oggi|SITO:https://www.youtube.com
Utente: "apri gmail youtube e spotify"       → MULTISTEP:SITO:https://mail.google.com|SITO:https://www.youtube.com|APRI:spotify
Utente: "come stai?"                         → RISPOSTA:Tutto bene, come posso aiutarti?
Utente: "che ore sono a tokyo?"              → RISPOSTA:A Tokyo sono le [calcola ora attuale + fuso]

REGOLE IMPORTANTI:
- NON aggiungere mai testo prima o dopo il comando
- NON spiegare cosa stai facendo
- NON usare formati diversi da quelli sopra
- Quando l utente chiede PIU cose insieme usa SEMPRE MULTISTEP separando con |
- Per i siti usa sempre l URL completo con https://
- Scegli sempre il formato piu appropriato'''

# ── VOCE EDGE TTS ────────────────────────────────────────────────
pygame.mixer.init()

async def _genera_audio(testo, percorso):
    """Genera il file audio con Edge TTS."""
    comunicatore = edge_tts.Communicate(testo, VOCE)
    await comunicatore.save(percorso)

def parla(testo):
    """Genera e riproduce la voce con Edge TTS."""
    try:
        # Crea file audio temporaneo
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            percorso = f.name

        # Genera audio con Edge TTS
        asyncio.run(_genera_audio(testo, percorso))

        # Riproduci con pygame
        pygame.mixer.music.load(percorso)
        pygame.mixer.music.play()

        # Aspetta che finisca
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Pulisci il file temporaneo
        pygame.mixer.music.unload()
        os.remove(percorso)

    except Exception as err:
        print(f">> Errore voce: {err}")

# ── ICONA SYSTEM TRAY ────────────────────────────────────────────
def crea_icona(colore):
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=colore)
    return img

COLORI = {
    "attesa":   (100, 100, 100, 255),
    "ascolto":  (50,  200, 50,  255),
    "pensiero": (255, 200, 0,   255),
    "errore":   (220, 50,  50,  255),
}

TOOLTIP = {
    "attesa":   f"Jarvis — Premi {TASTO} per parlare",
    "ascolto":  "Jarvis — Sto ascoltando...",
    "pensiero": "Jarvis — Sto pensando...",
    "errore":   "Jarvis — Errore, riprova",
}

icona_app = None

def aggiorna_icona(stato):
    global icona_app
    if icona_app is None:
        return
    icona_app.icon  = crea_icona(COLORI.get(stato, COLORI["attesa"]))
    icona_app.title = TOOLTIP.get(stato, "Jarvis")

def avvia_tray():
    global icona_app
    icona_app = pystray.Icon(
        "Jarvis",
        crea_icona(COLORI["attesa"]),
        TOOLTIP["attesa"],
        menu=pystray.Menu(
            pystray.MenuItem("Jarvis AI", lambda: None, enabled=False),
            pystray.MenuItem(f"Premi {TASTO} per parlare", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Esci", lambda: os._exit(0))
        )
    )
    icona_app.run()

# ── CARICAMENTO WHISPER ──────────────────────────────────────────
print("Carico Whisper...")
modello_whisper = whisper.load_model("base", device="cuda")
print(f"Jarvis pronto! Premi {TASTO} da qualsiasi app per parlare.\n")

# ── FUNZIONI PRINCIPALI ──────────────────────────────────────────
def registra_audio(durata=DURATA_REC, sample_rate=16000):
    audio = sounddevice.rec(
        int(durata * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sounddevice.wait()
    return audio.flatten()


def trascrivi(audio):
    result = modello_whisper.transcribe(audio, language=LINGUA)
    return result["text"].strip()


def chiedi_ai(testo):
    try:
        risposta = requests.post(OLLAMA_URL, json={
            "model":  MODEL,
            "stream": False,
            "prompt": f"{SYSTEM_PROMPT}\n\nUtente: {testo}"
        }, timeout=60)
        return risposta.json()["response"].strip()
    except Exception as e:
        return f"RISPOSTA:Errore di connessione con Ollama: {e}"


def esegui_azione(risposta):
    risposta = risposta.strip()

    # ── Azioni multiple ──────────────────────────────────────────
    if risposta.startswith("MULTISTEP:"):
        passi = risposta.split(":", 1)[1].strip().split("|")
        for passo in passi:
            passo = passo.strip()
            if passo:
                esegui_azione(passo)
        return

    # ── Apri app ─────────────────────────────────────────────────
    if risposta.startswith("APRI:"):
        app = risposta.split(":", 1)[1].strip().lower()
        if app in APP:
            try:
                subprocess.Popen(APP[app], shell=True)
                print(f">> Apro {app}")
                parla(f"Apro {app}")
            except Exception as e:
                print(f">> Errore nell'aprire {app}: {e}")
                parla(f"Non riesco ad aprire {app}")
        else:
            if app in SITI:
                webbrowser.open(SITI[app])
                print(f">> Apro sito {app}")
                parla(f"Apro {app}")
            else:
                print(f">> '{app}' non trovato.")
                parla(f"Non ho trovato {app} tra le app configurate")
        return

    # ── Cerca su Google ──────────────────────────────────────────
    if risposta.startswith("CERCA:"):
        query = risposta.split(":", 1)[1].strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        print(f">> Cerco: {query}")
        parla(f"Cerco {query} su Google")
        return

    # ── Apri sito ────────────────────────────────────────────────
    if risposta.startswith("SITO:"):
        url = risposta.split(":", 1)[1].strip()
        if url.lower() in SITI:
            url = SITI[url.lower()]
        webbrowser.open(url)
        print(f">> Apro: {url}")
        parla("Apro il sito")
        return

    # ── Risposta testuale ────────────────────────────────────────
    if risposta.startswith("RISPOSTA:"):
        testo = risposta.split(":", 1)[1].strip()
        print(f"\nJarvis: {testo}\n")
        parla(testo)
        return

    # ── Fallback ─────────────────────────────────────────────────
    print(f"\nJarvis: {risposta}\n")
    parla(risposta)


# ── GESTIONE TASTO ───────────────────────────────────────────────
in_elaborazione = False

def on_tasto():
    global in_elaborazione
    if in_elaborazione:
        return
    in_elaborazione = True

    try:
        aggiorna_icona("ascolto")
        winsound.Beep(800, 150)

        audio = registra_audio()

        winsound.Beep(500, 150)
        aggiorna_icona("pensiero")

        testo = trascrivi(audio)
        if not testo:
            print(">> Non ho capito, riprova.")
            parla("Non ho capito, riprova")
            return

        print(f"Tu: {testo}")
        risposta = chiedi_ai(testo)
        esegui_azione(risposta)

    except Exception as e:
        print(f">> Errore: {e}")
        aggiorna_icona("errore")
        winsound.Beep(300, 500)
        parla("Si è verificato un errore")

    finally:
        aggiorna_icona("attesa")
        in_elaborazione = False


def ascolta_tasto():
    keyboard.add_hotkey(TASTO, lambda: threading.Thread(target=on_tasto).start())
    keyboard.wait()


# ── AVVIO ────────────────────────────────────────────────────────
threading.Thread(target=ascolta_tasto, daemon=True).start()
parla("Jarvis pronto")
avvia_tray()