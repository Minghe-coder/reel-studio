---
name: reel-ingest
description: Crea un nuovo progetto video e importa i file grezzi (controllo formato, VFR, HDR, orientamento). Usala per "nuovo video", "importa i file", "ho messo i video in raw".
---
# Nuovo progetto e import

1. `python -m reel new <nome>` (nome breve, senza spazi: es. `trucchi-canva`).
2. Di' all'utente il percorso esatto di `projects/<nome>/raw/` dove copiare i video (B-roll e screenshot in `broll/`). Aspetta conferma.
3. `python -m reel ingest <nome>`. Leggi l'output:
   - file **VFR** (telefoni), **HDR/10 bit** o con fps diversi da 30 vengono convertiti in `work/` automaticamente;
   - **SENZA AUDIO**: avvisa (niente trascrizione per quel file);
   - **orizzontale**: verrà ritagliato al centro in 9:16. Proponi `--focus-y`/`focus_x` se il soggetto non è centrato.
4. Più file = più riprese: l'ordine è alfabetico. Se serve un ordine diverso, rinomina i file (01_, 02_...) e rifai l'ingest, oppure usa `--files` con l'ordine voluto.
5. Prossimo passo: skill reel-transcribe.
