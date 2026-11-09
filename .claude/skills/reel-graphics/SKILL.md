---
name: reel-graphics
description: Testi a schermo sincronizzati (hook, titoli, numeri, etichette, CTA), pop-up di immagini ed emoji, screenshot/B-roll, zoom punch-in, barra di avanzamento, colore/LUT. Usala per "testo", "titolo", "pop-up", "emoji", "zoom", "freccia", "screenshot", "CTA", "barra".
---
# Grafiche, testi e zoom

**Sincronizza sempre con le parole**: `--at "parola:X"` (inizio), `"fine:X"` (fine), `"parola:X#2"` (seconda volta), `-3` (3 s dalla fine), `-0` (fine del video). Prima verifica con `python -m reel find <nome> "X"`.

## Testi (`text`)
Stili in `config/brand.yaml` → `hook`, `title`, `cta`, `label`, `number`. Animazioni: `pop` (default), `fade`, `slide`, `typewriter`.
- Hook: `text <nome> "3 ERRORI CHE FAI" --at 0 --dur 3 --style hook` (massimo 6–7 parole).
- Numeri dei punti: `text <nome> "1" --at "parola:primo" --dur 1.2 --style number`.
- CTA: `text <nome> "Seguimi per la parte 2" --at -3 --end -0 --style cta`.
- Per andare a capo usa `\n` nel testo. Posizione verticale personalizzata: `--y 700`.

## Pop-up (`popup`)
- Emoji: `popup <nome> --emoji 🔥 --at "parola:gratis" --dur 1.2 --sfx sfx/pop/pop_1.wav` (scaricata automaticamente).
- Immagine/screenshot/B-roll statico: `popup <nome> --image assets/overlays/x.png --at ... --dur 3 --width 900 --y center --anim fade`.
- Default: x al centro, y=760 (sopra i sottotitoli), larghezza 380 px. Evita le zone rosse.
- Ogni pop-up deve avere un SFX leggero (pop/click), a meno che l'utente dica di no.

## Zoom
- Jump cut dinamico: `autozoom <nome>` (punch-in 1.12x alternati, spezza i pezzi più lunghi di 4,5 s).
- Enfasi: `zoom <nome> --from "parola:attenzione" --to "fine:importante" --factor 1.3`.
- Inquadratura (soprattutto da video orizzontale): `--focus-y 0.3` sposta il ritaglio verso l'alto, cioè sul viso.

## Altro
- Barra di avanzamento: `progress <nome> on` (`--position bottom` la mette sotto, ma lì può finire sotto l'interfaccia dell'app).
- Colore: in `edl.json` → `color` (`lut`: `assets/luts/x.cube`; `saturation` 1.1; `contrast` 1.05).
- Rimuovere: `remove <nome> popups 0` (gli indici si leggono con `show`).
- Animazioni più complesse (liste animate, contatori, lower third elaborati): fase 2 con Remotion. Dillo all'utente invece di forzare FFmpeg.

Densità consigliata: un elemento grafico ogni 3–5 s, mai più di 2 elementi a schermo oltre ai sottotitoli.
