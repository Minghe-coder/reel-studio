---
name: reel-audio
description: Audio del reel - pulizia voce, musica di sottofondo dalla libreria royalty-free con ducking, effetti sonori sincronizzati, loudness -14 LUFS. Usala per "musica", "effetto sonoro", "SFX", "volume", "pulisci la voce", "boom", "whoosh".
---
# Audio

## Voce (automatico in ogni render)
Filtro passa-alto 80 Hz → denoise (`afftdn`) → EQ (meno rimbombo a 250 Hz, più presenza a 3,5 kHz) → compressore → loudnorm a **-14 LUFS / -1.5 dBTP**, con un secondo passaggio di correzione nel render finale.
Si disattiva in `edl.json` → `audio` (`denoise`, `voice_eq`, `compress`): utile se la voce suona "metallica" (togli denoise).

## Musica
1. Leggi `assets/music/music_catalog.csv` (se non esiste o è vecchio: `python -m reel catalog`). Proponi 2–3 brani adatti al mood e alla durata, con una domanda interattiva. **Controlla la colonna licenza**: se è vuota, chiedi all'utente.
2. `python -m reel music <nome> assets/music/chill/brano.mp3 --volume 0.15` (parlato: 0.10–0.18; video solo musica: 0.6–0.9 con `--no-duck`).
3. Il ducking (sidechain) abbassa la musica quando parli. Il brano va in loop se è più corto del video, con fade in e fade out automatici.
4. `--start 42` fa partire il brano dal secondo 42 (il drop o il ritornello).
5. Se l'utente vuole usare un audio di tendenza: `music <nome> --off` e ricordagli di aggiungerlo dall'app.

## Effetti sonori
- `python -m reel sfx <nome> sfx/boom/boom_1.wav --at 0 --volume 0.8`
- Mappa consigliata: hook → boom · pop-up → pop · cambio argomento → whoosh · numero/elenco → click · CTA o "salva" → ding · testo typewriter → typing · errore/fail → glitch.
- Volume: 0.5–0.9. Non più di un SFX ogni 2 s, altrimenti stanca.
- Elenco disponibili: `assets/sfx/sfx_catalog.csv`.
