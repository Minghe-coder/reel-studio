---
name: reel-captions
description: Sottotitoli animati sincronizzati parola per parola (preset bold, clean, pop), parole chiave evidenziate, correzioni, emoji. Usala per "sottotitoli", "evidenzia", "correggi la parola", "cambia stile ai sottotitoli".
---
# Sottotitoli

Preset in `config/caption_presets.yaml`:
- **bold**: 3 parole max, MAIUSCOLO, parola pronunciata in giallo e più grande. Il default per i video parlati.
- **clean**: frase intera su riquadro scuro, sobrio. Adatto a tutorial e brand eleganti.
- **pop**: 1–2 parole giganti che compaiono con un "pop". Massima energia.

Procedura:
1. Se l'utente non ha scelto, proponi i 3 preset con una domanda interattiva. Se è indeciso: fai 3 anteprime brevi (`preview --name prova_bold.mp4` ecc., cambiando preset) e mostragliele.
2. `python -m reel captions <nome> --preset bold`.
3. Parole chiave: scegli 1 parola ogni 3–5 secondi tra numeri, soldi, risultati e negazioni forti, e proponile → `--highlight parola1 parola2`.
4. Correzioni: `--replace "sbagliato=giusto"` (la chiave è la parola come trascritta).
5. Emoji sotto una parola: `--emoji "soldi=💰"` (con moderazione).
6. Personalizzazioni (colore, dimensione, posizione) per un solo video: aggiungi in `edl.json` → `captions.overrides` (es. `{"y": 1150, "active_color": "#00E676"}`). Per tutti i video: modifica il preset nello YAML.
7. Posizione: `y` è il centro dei sottotitoli. Resta tra 1100 e 1400 (sopra la zona bassa di 400 px). Se c'è un testo `hook` o un pop-up nella stessa zona, sposta uno dei due.
