# 🤖 Jarvis AI — Assistente Vocale Personale per Windows

Un assistente AI vocale personale ispirato a Jarvis di Iron Man, che gira **completamente in locale** sul tuo PC Windows — nessun abbonamento, nessun limite di messaggi.

---

## ✨ Funzionalità

- 🎤 **Riconoscimento vocale** tramite OpenAI Whisper (accelerato su GPU)
- 🧠 **Intelligenza artificiale locale** con Mistral 7B via Ollama
- 🔊 **Risposta vocale** naturale con Microsoft Edge TTS (voce `it-IT-DiegoNeural`)
- 🖥️ **Controllo del PC** — apre app, cerca su Google, naviga tra siti
- ⚡ **Comandi multipli** — esegue più azioni con un solo comando vocale
- 🔵 **Icona nella system tray** che cambia colore in base allo stato
- 🎯 **Attivazione con tasto** — premi F12 da qualsiasi app per parlare
- 💨 **Zero impatto sui giochi** — quando non lo usi, non consuma risorse

---

## 🛠️ Tecnologie utilizzate

| Componente | Tecnologia | Scopo |
|---|---|---|
| Riconoscimento vocale | OpenAI Whisper | Converte la voce in testo |
| Intelligenza artificiale | Mistral 7B (Ollama) | Elabora i comandi e decide le azioni |
| Sintesi vocale | Microsoft Edge TTS | Genera la risposta vocale |
| Riproduzione audio | Pygame | Riproduce l'audio generato |
| Interfaccia sistema | Pystray + Pillow | Icona nella barra di sistema |
| Hotkey globale | Keyboard | Rileva F12 da qualsiasi app |
| Linguaggio | Python 3.11 | Linguaggio principale |

---

## 💻 Requisiti

- Windows 10/11
- Python 3.11+
- RAM: 16 GB consigliati
- GPU: 4+ GB VRAM consigliati (per accelerare Whisper)
- Connessione internet (solo per la voce Edge TTS)
- ~8 GB di spazio libero su disco

---

## 📦 Installazione

### 1. Clona il repository
```bash
git clone https://github.com/Santogg0/jarvis-ai-assistant.git
cd jarvis-ai-assistant
```

### 2. Installa le dipendenze Python
```bash
pip install openai-whisper sounddevice numpy requests keyboard pystray pillow edge-tts pygame
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Installa Ollama e scarica il modello AI
```bash
# Scarica Ollama da https://ollama.com/download
ollama pull mistral:7b-instruct-q4_0
```

### 4. Avvia Jarvis
```bash
python jarvis.py
```

---

## 🎮 Come si usa

| Azione | Risultato |
|---|---|
| Premi **F12** | Jarvis inizia ad ascoltare (bip + icona verde) |
| Parla per ~4 secondi | Jarvis elabora il comando (bip + icona gialla) |
| Jarvis risponde | Esegue l'azione e risponde a voce (icona grigia) |

### Esempi di comandi vocali

```
"Apri Chrome"                    → Apre Google Chrome
"Apri Spotify"                   → Apre Spotify
"Vai su YouTube"                 → Apre YouTube nel browser
"Apri YouTube e Gmail"           → Apre entrambi
"Cerca meteo domani"             → Cerca su Google
"Apri Chrome e Spotify"         → Esegue entrambe le azioni
"Che ore sono a Tokyo?"          → Risponde a voce
```

---

## 🏗️ Architettura del sistema

```
[Tasto F12]
     │
     ▼
[Whisper - GPU]          ← registra e trascrive la voce
     │
     ▼
[Ollama + Mistral 7B]    ← capisce il comando e decide l'azione
     │
     ▼
[Script Python]          ← esegue l'azione sul PC
     │
     ▼
[Edge TTS + Pygame]      ← risponde a voce
```

---

## ⚙️ Configurazione

Puoi personalizzare il file `jarvis.py` modificando:

- `TASTO` — cambia il tasto di attivazione (default: F12)
- `DURATA_REC` — durata registrazione in secondi (default: 4)
- `VOCE` — voce Edge TTS (default: `it-IT-DiegoNeural`)
- `APP` — dizionario delle app apribili
- `SITI` — dizionario dei siti rapidi

---

## 🚀 Avvio automatico con Windows

Crea un file `avvia_jarvis.vbs` con questo contenuto:
```vbs
Set objShell = CreateObject("WScript.Shell")
objShell.Run "python C:\percorso\jarvis.py", 0, False
```
Salvalo nella cartella di avvio automatico: `shell:startup`

---

## 👤 Autore

Sviluppato da **Santogg0** come progetto personale extrascolastico.

---

## 📄 Licenza

Progetto a uso personale ed educativo.
