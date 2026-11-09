---
name: reel-rough-cut
description: Taglio grezzo e tagli manuali - silenzi, intercalari (ehm), riprese sbagliate, frasi da eliminare, spostamenti, durata target. Usala per "taglia", "togli", "elimina la frase", "tieni l'ultima ripresa", "accorcia".
---
# Taglio grezzo e tagli

## Automatico
1. `python -m reel autocut <nome> --level normale` (`leggero` = più naturale, `aggressivo` = ritmo TikTok). Leggi il report: durata prima/dopo, % tagliata, intercalari rimossi.
   - Se viene tagliato più del 45% o si tagliano parole: `--level leggero` o una soglia esplicita `--threshold -40` (microfono basso) / `-30` (stanza rumorosa).
2. **Riprese sbagliate**: dalla trascrizione individua le frasi ripetute (stesse parole iniziali a pochi secondi di distanza, o frasi interrotte). Mostra all'utente l'elenco "ripresa 1 (scarto) / ripresa 2 (tengo)" e chiedi conferma, poi `python -m reel cut <nome> --phrase "testo della ripresa scartata" --n 1`. Usa poche parole iniziali uniche della frase; per frasi interrotte usa `find` e poi `cut --from --to` con i tempi d'uscita.
3. `python -m reel show <nome>`: mostra l'elenco dei pezzi con il testo. Controlla che non ci siano parole tronche; correggi con `trim <i> --head/--tail` (valori negativi = allunga).

## Manuale
- Intervallo: `cut --from 0:12.4 --to 0:15` (tempi della timeline **attuale**, ricavali da `show`).
- Frase: `cut --phrase "..."` (`--all` per tutte le occorrenze).
- Spostare l'hook all'inizio: `move --from "parola:ecco" --to "fine:risultato" --dest 0`.
- Durata target: proponi tu cosa togliere (frasi meno utili), con tempi e testo, e chiedi conferma prima di tagliare.

Tutto è annullabile con `undo`. Dopo i tagli fai una `preview` se l'utente vuole sentire il ritmo.
