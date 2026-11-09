# Reel Studio: istruzioni per Claude

Progetto per montare video **verticali 9:16** (Instagram Reels, TikTok) partendo dai video grezzi dell'utente.
L'utente è **alle prime armi con il montaggio**: parla in italiano, spiega ogni passo in modo semplice, proponi e chiedi conferma prima delle scelte creative importanti (usa le domande interattive con opzioni).

## Regole d'oro
1. **Non modificare mai** i file in `projects/<nome>/raw/`. Tutto il montaggio sta in `projects/<nome>/edl.json`.
2. Modifica l'EDL **con la CLI** (`python -m reel ...`): è testata e salva lo storico per `undo`. Modifica `edl.json` a mano solo per ciò che la CLI non copre, rispettando lo schema in `reel/edl.py`.
3. Per sincronizzare testi, pop-up e SFX al parlato usa gli anchor a parola (`--at "parola:gratis"`), non i secondi: così restano agganciati anche se poi si ritaglia.
4. Prima del render finale fai **sempre un'anteprima** (`preview`) e descrivi all'utente cosa contiene. Dopo il render finale leggi il report QC e guarda i fotogrammi in `out/qc/` (zone sicure in rosso).
5. Testi importanti fuori dalle zone rosse: alto 250 px, basso 400 px, destra 150 px (tela 1080x1920).
6. Stile di default: ritmo serrato (un cambio visivo ogni 2–4 s), effetti usati con misura. Non mettere transizioni flash/whoosh su ogni taglio se l'utente non lo chiede.
7. Musica: solo da `assets/music` (royalty-free, licenza annotata nel catalogo). Se la licenza è vuota, chiedi all'utente.
8. Se un comando fallisce, leggi l'errore, spiega in parole semplici e proponi la soluzione.

## Flusso standard di un video
`new` → l'utente copia i file in `raw/` → `ingest` → `transcribe` → `autocut` → (rivedi i tagli con `show`) → `captions` → testi/pop-up/zoom/SFX/musica → `preview` → correzioni → `render` → caption e hashtag del post.

## Mappa delle skill (`.claude/skills/`)
reel-setup · reel-script · reel-ingest · reel-transcribe · reel-rough-cut · reel-captions · reel-graphics · reel-audio · reel-transitions · reel-render

## Riferimenti
- Comandi dell'utente → `COMANDI.md`
- Schema EDL e anchor → `reel/edl.py`
- Preset sottotitoli → `config/caption_presets.yaml`; stili testo e colori brand → `config/brand.yaml`; specifiche export → `config/export.yaml`
- Test: `python -m pytest -q tests`
