---
name: reel-setup
description: Installa e verifica l'ambiente di Reel Studio (FFmpeg, Python, faster-whisper, font, SFX). Usala quando l'utente installa il progetto, quando un comando fallisce per mancanza di programmi, o quando chiede "è tutto pronto?".
---
# Setup e diagnostica

1. Esegui `python -m reel doctor` e leggi l'output riga per riga.
2. Per ogni riga `!!` spiega in parole semplici cosa manca e dai il comando esatto da SETUP-WINDOWS.md (un comando per blocco di codice). L'utente usa Windows (Boot Camp su Mac Intel, niente GPU NVIDIA).
3. Se mancano gli SFX: `python -m reel sfx-base`. Se mancano i cataloghi: `python -m reel catalog`.
4. Verifica che il virtualenv sia attivo (`.venv`). Se `python -m reel` dà `ModuleNotFoundError: yaml`, il venv non è attivo.
5. Test opzionale completo: `python -m pytest -q tests` (circa 15 s, crea e cancella un progetto di prova).
6. Alla fine riepiloga: cosa funziona, cosa manca, prossimo passo (di solito MATERIALI.md).
