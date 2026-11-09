---
name: reel-transitions
description: Transizioni tra le scene - jump cut, flash bianco, dip al nero, whoosh sonoro, sui tagli o su parole precise. Usala per "transizione", "flash", "whoosh tra i punti", "dissolvenza".
---
# Transizioni

Nei reel parlati la transizione migliore è quasi sempre il **jump cut** (taglio netto + punch-in: `autozoom`). Le transizioni "evidenti" vanno solo sui **cambi di argomento**.

- Flash + whoosh su un cambio di argomento:
  `python -m reel transition <nome> --type flash --at "parola:secondo" --sfx sfx/whoosh/whoosh_1.wav`
- Solo suono sui tagli (molto usato su TikTok): `transition <nome> --type none --all-cuts --sfx sfx/whoosh/whoosh_2.wav` (sconsigliato se i tagli sono più di 8–10).
- Dissolvenza al nero breve (cambio scena, prima della CTA): `--type dip`.
- Flash colorato: in `edl.json` aggiungi `"color": "#FFD400"`, `"opacity": 0.6` alla transizione.
- Il whoosh parte 0,15 s prima del taglio (`sfx_lead`) perché suoni naturale.

Per transizioni complesse (whip pan, glitch visivo, slide tra due clip con xfade) serve la fase 2 o una modifica alla pipeline: proponila all'utente se le chiede spesso.
