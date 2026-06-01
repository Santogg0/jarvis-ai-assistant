# ============================================================
#  JARVIS AI — Assistente Vocale Personale per Windows
#  Autore: Santogg0
#  GitHub: https://github.com/Santogg0/jarvis-ai-assistant
#
#  Come funziona:
#  1. Premi F10 da qualsiasi applicazione
#  2. Parla per 4 secondi
#  3. Whisper trascrive la voce in testo
#  4. Mistral AI capisce il comando e decide l'azione
#  5. Lo script esegue l'azione sul PC
#  6. Edge TTS risponde a voce
# ============================================================

import whisper        # riconoscimento vocale
import sounddevice    # registrazione audio dal microfono
import numpy as np
import requests       # comunicazione con Ollama
import subprocess     # apertura applicazioni Windows
import os
import webbrowser     # apertura siti web
import winsound       # bip di conferma
import keyboard       # rilevamento tasto F10
import threading      # gestione processi in parallelo
import pystray        # icona nella barra di sistema
import asyncio
import tempfile
import edge_tts       # voce AI di Microsoft
import pygame         # riproduzione audio
from PIL import Image, ImageDraw

# ── CONFIGURAZIONE PRINCIPALE ────────────────────────────────────
# Indirizzo locale di Ollama (non serve internet)
OLLAMA_URL  = "http://localhost:11434/api/generate"

# Modello AI da usare (versione leggera e veloce di Mistral)
MODEL       = "mistral:7b-instruct-q4_0"

# Lingua per il riconoscimento vocale
LINGUA      = "it"

# Tasto per attivare Jarvis (cambia qui se vuoi un altro tasto)
TASTO       = "F10"

# Secondi di registrazione audio (4 bastano per comandi brevi)
DURATA_REC  = 4

# Voce italiana maschile di Microsoft Edge
VOCE        = "it-IT-DiegoNeural"

# ── APP CONFIGURATE ──────────────────────────────────────────────
# Dizionario delle app che Jarvis può aprire
# Formato: "nome che dici" : "comando Windows"
APP = {
    "chrome":             "start chrome",
    "firefox":            "start firefox",
    "spotify":            "start spotify:",
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
# Dizionario dei siti web che Jarvis conosce già
# Formato: "nome che dici" : "url completo"
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

# ── ISTRUZIONI PER IL MODELLO AI ─────────────────────────────────
# Questo testo viene inviato a Mistral ad ogni richiesta per
# insegnargli come deve rispondere (sempre con comandi formattati)
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
Utente: "come stai?"                         → RISPOSTA:Tutto bene, come posso aiutarti?

REGOLE IMPORTANTI:
- NON aggiungere mai testo prima o dopo il comando
- NON spiegare cosa stai facendo
- NON usare formati diversi da quelli sopra
- Quando l utente chiede PIU cose insieme usa SEMPRE MULTISTEP separando con |
- Per i siti usa sempre l URL completo con https://
- Scegli sempre il formato piu appropriato'''

# ── VOCE AI (EDGE TTS) ───────────────────────────────────────────
# Inizializza il sistema audio di pygame
pygame.mixer.init()

async def _genera_audio(testo, percorso):
    """Genera il file audio MP3 con Edge TTS di Microsoft."""
    comunicatore = edge_tts.Communicate(testo, VOCE)
    await comunicatore.save(percorso)

def parla(testo):
    """Fa parlare Jarvis a voce usando Edge TTS.
    
    Il processo è:
    1. Crea un file audio temporaneo
    2. Edge TTS lo riempie con la voce generata
    3. Pygame lo riproduce
    4. Il file temporaneo viene cancellato
    """
    try:
        # Crea un file temporaneo per l'audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            percorso = f.name

        # Genera l'audio con Edge TTS
        asyncio.run(_genera_audio(testo, percorso))

        # Riproduci con pygame
        pygame.mixer.music.load(percorso)
        pygame.mixer.music.play()

        # Aspetta che finisca la riproduzione
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Pulisci il file temporaneo
        pygame.mixer.music.unload()
        os.remove(percorso)

    except Exception as err:
        print(f">> Errore voce: {err}")

# ── ICONA NELLA BARRA DI SISTEMA ─────────────────────────────────
# L'icona cambia colore in base allo stato di Jarvis:
# Grigio  = in attesa (premi F10 per parlare)
# Verde   = sta ascoltando
# Giallo  = sta elaborando la risposta
# Rosso   = si è verificato un errore

def crea_icona(colore):
    """Crea un cerchio colorato da usare come icona nella tray."""
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=colore)
    return img

COLORI = {
    "attesa":   (100, 100, 100, 255),   # grigio
    "ascolto":  (50,  200, 50,  255),   # verde
    "pensiero": (255, 200, 0,   255),   # giallo
    "errore":   (220, 50,  50,  255),   # rosso
}

TOOLTIP = {
    "attesa":   f"Jarvis — Premi {TASTO} per parlare",
    "ascolto":  "Jarvis — Sto ascoltando...",
    "pensiero": "Jarvis — Sto pensando...",
    "errore":   "Jarvis — Errore, riprova",
}

icona_app = None

def aggiorna_icona(stato):
    """Aggiorna il colore e il testo dell'icona nella barra di sistema."""
    global icona_app
    if icona_app is None:
        return
    icona_app.icon  = crea_icona(COLORI.get(stato, COLORI["attesa"]))
    icona_app.title = TOOLTIP.get(stato, "Jarvis")

def avvia_tray():
    """Avvia l'icona nella barra di sistema con il menu contestuale."""
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
# Carica il modello Whisper sulla GPU (device="cuda") per maggiore velocità
# La prima volta ci vuole qualche minuto per scaricare il modello
print("Carico Whisper sulla GPU...")
modello_whisper = whisper.load_model("base", device="cuda")
print(f"Jarvis pronto! Premi {TASTO} da qualsiasi app per parlare.\n")

# ── REGISTRAZIONE AUDIO ──────────────────────────────────────────
def registra_audio(durata=DURATA_REC, sample_rate=16000):
    """Registra l'audio dal microfono per il numero di secondi configurato."""
    audio = sounddevice.rec(
        int(durata * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sounddevice.wait()  # aspetta che finisca la registrazione
    return audio.flatten()

# ── TRASCRIZIONE VOCALE ──────────────────────────────────────────
def trascrivi(audio):
    """Converte l'audio registrato in testo usando Whisper."""
    result = modello_whisper.transcribe(audio, language=LINGUA)
    return result["text"].strip()

# ── COMUNICAZIONE CON L'AI ───────────────────────────────────────
def chiedi_ai(testo):
    """Manda il testo al modello Mistral e ottiene il comando da eseguire."""
    try:
        risposta = requests.post(OLLAMA_URL, json={
            "model":  MODEL,
            "stream": False,
            "prompt": f"{SYSTEM_PROMPT}\n\nUtente: {testo}"
        }, timeout=60)
        return risposta.json()["response"].strip()
    except Exception as e:
        return f"RISPOSTA:Errore di connessione con Ollama: {e}"

# ── ESECUZIONE DELLE AZIONI ──────────────────────────────────────
def esegui_azione(risposta):
    """Interpreta la risposta dell'AI ed esegue l'azione corrispondente sul PC."""
    risposta = risposta.strip()

    # Azioni multiple: esegue ogni comando separato dal simbolo |
    if risposta.startswith("MULTISTEP:"):
        passi = risposta.split(":", 1)[1].strip().split("|")
        for passo in passi:
            passo = passo.strip()
            if passo:
                esegui_azione(passo)  # chiama se stesso per ogni azione
        return

    # Apre un'applicazione configurata nel dizionario APP
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
            # Se non trova l'app, prova nel dizionario dei siti
            if app in SITI:
                webbrowser.open(SITI[app])
                print(f">> Apro sito {app}")
                parla(f"Apro {app}")
            else:
                print(f">> '{app}' non trovato.")
                parla(f"Non ho trovato {app} tra le app configurate")
        return

    # Cerca qualcosa su Google
    if risposta.startswith("CERCA:"):
        query = risposta.split(":", 1)[1].strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        print(f">> Cerco: {query}")
        parla(f"Cerco {query} su Google")
        return

    # Apre un sito web nel browser predefinito
    if risposta.startswith("SITO:"):
        url = risposta.split(":", 1)[1].strip()
        if url.lower() in SITI:
            url = SITI[url.lower()]
        webbrowser.open(url)
        print(f">> Apro: {url}")
        parla("Apro il sito")
        return

    # Risponde a voce a una domanda normale
    if risposta.startswith("RISPOSTA:"):
        testo = risposta.split(":", 1)[1].strip()
        print(f"\nJarvis: {testo}\n")
        parla(testo)
        return

    # Fallback: se il formato non è riconosciuto, mostra e legge la risposta
    print(f"\nJarvis: {risposta}\n")
    parla(risposta)

# ── GESTIONE DEL TASTO F10 ───────────────────────────────────────
# Questa variabile evita che Jarvis si attivi due volte contemporaneamente
in_elaborazione = False

def on_tasto():
    """Viene chiamata ogni volta che l'utente preme F10."""
    global in_elaborazione

    # Se sta già elaborando un comando, ignora la pressione
    if in_elaborazione:
        return
    in_elaborazione = True

    try:
        # Fase 1: ascolto
        aggiorna_icona("ascolto")
        winsound.Beep(800, 150)          # bip acuto = inizia ad ascoltare
        audio = registra_audio()

        # Fase 2: elaborazione
        winsound.Beep(500, 150)          # bip grave = ha smesso di ascoltare
        aggiorna_icona("pensiero")

        # Trascrivi l'audio in testo
        testo = trascrivi(audio)
        if not testo:
            print(">> Non ho capito, riprova.")
            parla("Non ho capito, riprova")
            return

        # Mostra cosa ha capito e manda all'AI
        print(f"Tu: {testo}")
        risposta = chiedi_ai(testo)
        esegui_azione(risposta)

    except Exception as e:
        print(f">> Errore: {e}")
        aggiorna_icona("errore")
        winsound.Beep(300, 500)
        parla("Si è verificato un errore")

    finally:
        # Torna sempre allo stato di attesa alla fine
        aggiorna_icona("attesa")
        in_elaborazione = False

def ascolta_tasto():
    """Thread in background che ascolta la pressione di F10."""
    keyboard.add_hotkey(TASTO, lambda: threading.Thread(target=on_tasto).start())
    keyboard.wait()

# ── AVVIO DEL PROGRAMMA ──────────────────────────────────────────
# Avvia il listener del tasto in un thread separato (non blocca il programma)
threading.Thread(target=ascolta_tasto, daemon=True).start()

# Messaggio di benvenuto a voce
parla("Jarvis pronto")

# Avvia l'icona nella barra di sistema (questo blocca il thread principale)
avvia_tray()