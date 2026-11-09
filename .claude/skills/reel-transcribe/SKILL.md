---
name: reel-transcribe
description: Trascrive l'audio con faster-whisper ottenendo i tempi di ogni parola (base per tagli, sottotitoli e sincronizzazione). Usala per "trascrivi", "correggi la trascrizione", "cosa dico al secondo X".
---
# Trascrizione parola per parola

1. Prima di trascrivere controlla `config/glossario.txt`: aggiungi nomi propri, brand e termini tecnici del video.
2. `python -m reel transcribe <nome>` (modello `medium` di default, CPU int8). Per prove veloci: `--model small`. Se la qualità è scarsa: `--model large-v3` (lento).
3. Leggi `projects/<nome>/transcript.txt` e fai un controllo rapido: parole sbagliate, nomi propri. Correggi:
   - per i sottotitoli: `captions --replace "sbagliato=giusto"`;
   - se gli errori sono molti: aggiungi i termini al glossario e ritrascrivi.
4. Nota tecnica: la CLI rileva i silenzi e accorcia la fine delle parole che Whisper allunga dentro le pause (errore noto), così tagli e sottotitoli sono precisi.
5. Mostra all'utente la trascrizione con i tempi e segnala le **frasi ripetute** (riprese sbagliate): servono per il taglio.
