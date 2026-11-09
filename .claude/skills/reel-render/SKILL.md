---
name: reel-render
description: Anteprima veloce e export finale 1080x1920 H.264 per Instagram Reels/TikTok, controllo qualità (risoluzione, fps, loudness, zone sicure) e varianti. Usala per "anteprima", "render", "esporta", "controlla il video".
---
# Anteprima, render e controllo qualità

1. `python -m reel show <nome>`: controlla la presenza di `PROBLEMI` prima di renderizzare.
2. **Anteprima**: `python -m reel preview <nome>` → `out/preview.mp4` (540x960, veloce). Descrivi all'utente cosa c'è secondo per secondo (hook, testi, pop-up, musica) e chiedi le correzioni.
3. **Finale**: `python -m reel render <nome>` → `out/final.mp4` (1080x1920, 30 fps, H.264 High, CRF 18, AAC 192k, -14 LUFS, faststart). Il QC parte da solo.
4. Leggi il report QC: la lista `problems` deve essere vuota. Apri (Read) i fotogrammi `out/qc/frame_*.jpg`: le bande rosse sono le zone coperte dall'interfaccia dell'app. Se ci sono testi importanti sotto le bande, sposta (`y`) e rifai il render.
5. Varianti utili:
   - senza musica (per gli audio di tendenza): `music --off`, poi `render --name final_no_music.mp4`, poi `undo`;
   - senza sottotitoli: `captions --off`, poi `render --name final_no_sub.mp4`, poi `undo`.
6. In caso di errore FFmpeg: il comando completo è in `out/last_command.json` e il filtro in `out/filtergraph.txt`. Le cause più comuni sono un file asset mancante o un anchor a una parola tagliata.
7. Alla fine ricorda: copiare `final.mp4` sul telefono (Google Drive, AirDrop dal Mac o cavo), scegliere la copertina in app e usare la caption da `out/post.md` (skill reel-script).
