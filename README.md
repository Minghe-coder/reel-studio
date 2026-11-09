# Reel Studio 🎬

Monta i tuoi video verticali per **Instagram Reels e TikTok** parlando con Claude Code.
Tu giri il video e dici cosa vuoi ("taglia i silenzi", "metti il titolo quando dico X", "aggiungi musica chill").
Claude trascrive, taglia, aggiunge sottotitoli animati, grafiche, effetti sonori e musica, ed esporta il file pronto da pubblicare.

## Da dove partire
1. **Installazione** → [SETUP-WINDOWS.md](SETUP-WINDOWS.md)
2. **Materiali** (musica, effetti, font, logo) → [MATERIALI.md](MATERIALI.md)
3. **Cosa dire a Claude** → [COMANDI.md](COMANDI.md)
4. **Come scrivere e girare il video** → [GUIDA-VIDEO.md](GUIDA-VIDEO.md)

## Come funziona (in breve)
```
raw/ (i tuoi video)  →  trascrizione (Whisper, parola per parola)
                     →  edl.json (il montaggio come lista di istruzioni)
                     →  FFmpeg  →  out/final.mp4 (1080x1920, 30fps, -14 LUFS)
```
Il video originale non viene mai toccato. Ogni modifica si può annullare (`undo`).

## Struttura
| Cartella | Contenuto |
|---|---|
| `projects/<nome>/` | un progetto per video: `raw/`, `scaletta.md`, `transcript.txt`, `edl.json`, `out/` |
| `assets/` | musica, effetti sonori, font, immagini, emoji, LUT colore |
| `config/` | specifiche di export, preset sottotitoli, colori del brand, glossario |
| `reel/` | il motore (Python + FFmpeg) |
| `.claude/skills/` | le procedure che Claude segue per ogni fase |
