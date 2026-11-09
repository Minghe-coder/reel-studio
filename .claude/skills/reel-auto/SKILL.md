---
name: reel-auto
description: Pilota automatico - monta un reel completo dai video nella cartella del Desktop "1 - Video da montare" con poche domande a schede, apre l'anteprima e mostra il menu dei comandi. Usala per "monta il video", "nuovo reel", "ho messo un video", "Ciao! Avvia Reel Studio", "aiuto", "cosa posso dire", e quando l'utente non sa da dove iniziare.
---
# Pilota automatico (per chi non usa il terminale)

L'utente NON è tecnico: non mostrare mai comandi, percorsi lunghi o JSON. Frasi brevi, tono amichevole, emoji con misura. Per le scelte usa SEMPRE le schede interattive (AskUserQuestion) con 2–4 opzioni chiare; metti per prima l'opzione consigliata.
Se `python -m reel` fallisce con `ModuleNotFoundError`, usa `.venv/Scripts/python -m reel` (Windows) per tutta la sessione.

## 0. Benvenuto ("Ciao! Avvia Reel Studio")
Esegui `python -m reel inbox`.
- Se ci sono video da montare, dillo ("Ho trovato 1 video: IMG_1234, 42 secondi") e proponi con una scheda: **Montalo ora (consigliato)** / Continua un video già iniziato / Mostrami cosa posso fare.
- Se è vuota: spiega in 2 righe come mettere i video nella cartella *Reel Studio → 1 - Video da montare* sul Desktop (dall'iPhone: cavo USB e app Foto di Windows, oppure WhatsApp **inviato come Documento** per non perdere qualità, oppure iCloud.com). Apri la cartella con `python -m reel open da-montare`. Proponi di continuare un progetto recente se ce ne sono.

## 1. Domande iniziali (UNA sola scheda con max 4 domande)
Prima di chiedere, fai la trascrizione così puoi proporre hook sensati: crea il progetto con nome automatico `AAAA-MM-GG-parola` (data di oggi + una parola dal nome del file o "reel") usando `python -m reel new <nome> --from-inbox`, poi `python -m reel transcribe <nome>` (avvisa: "ci vuole qualche minuto, la prima volta scarica il modello"). Se ci sono più video, chiedi prima l'ordine solo se dai nomi dei file non è ovvio.
Poi chiedi con un'unica scheda:
1. **Stile sottotitoli**: Bold (parola evidenziata, energico) · Clean (frase elegante) · Pop (parole giganti).
2. **Testo d'apertura (hook)**: 3 proposte scritte da te in base alla trascrizione (max 6 parole), più "nessun testo"; può scriverne uno suo con "Altro".
3. **Musica**: i mood disponibili nella libreria (`assets/music/music_catalog.csv`) + "Nessuna, la metto da Instagram/TikTok". Se la libreria è vuota, chiedi solo se vuole effetti sonori: Sì, con misura (consigliato) / No.
4. **Finale (CTA)**: "Seguimi per altri consigli" · "Salva questo video" · "Commenta …" (adatta all'argomento) · nessuno.

## 2. Montaggio automatico (senza chiedere)
1. `autocut --level normale`; poi trova le riprese ripetute nella trascrizione e tieni l'ultima (`cut --phrase ... --n 1`), senza chiedere, ma elencale nel riepilogo.
2. `autozoom`.
3. `captions --preset <scelto>` con 3–6 parole chiave evidenziate (numeri, risultati, parole forti); correggi eventuali errori evidenti della trascrizione con `--replace`.
4. Hook: `text "<hook>" --at 0 --dur 3 --style hook` + `sfx sfx/boom/boom_1.wav --at 0 --volume 0.6`.
5. Se il video elenca punti ("primo", "secondo", "1", "2"...): numeri `--style number` sincronizzati + click.
6. 1–3 pop-up emoji su parole emotive (non di più), ognuno con `sfx/pop/pop_1.wav`.
7. Musica: brano del mood scelto con durata adatta, volume 0.12, ducking attivo (`music ...`). Se manca la licenza nel catalogo, non usarlo e dillo.
8. CTA: `text "<cta>" --at -3 --end -0 --style cta` + ding.
9. `preview --open` (apre il video da solo).

## 3. Dopo l'anteprima: riepilogo + MENU
Riepilogo in 4–6 righe: durata prima → dopo, cosa hai tagliato (riprese, pause, "ehm"), cosa hai aggiunto. Poi mostra SEMPRE questo menu (adattando gli esempi al video):

> **Cosa vuoi cambiare? Scrivimelo con parole tue, per esempio:**
> ✂️ "togli la parte in cui dico …" · "taglia meno / taglia di più"
> 💬 "sottotitoli più grandi / più in basso / stile pop" · "correggi la parola …"
> 🅰️ "cambia il titolo in …" · "aggiungi la scritta … quando dico …"
> ✨ "metti un'emoji 😍 quando dico …" · "togli le emoji"
> 🔊 "musica più bassa / più alta / un'altra musica" · "togli gli effetti sonori"
> 🔍 "meno zoom" · "più movimento"
> ✅ **"va bene così"** → preparo il video finale
> ❓ "aiuto" → ti rimostro questo menu

Ad ogni correzione: modifica, nuova `preview --open`, breve conferma di cosa hai cambiato e il menu in versione corta (3 righe + "va bene così").

## 4. "Va bene così" → video finale
1. `render` (copia automaticamente in *Reel Studio → 2 - Video pronti* sul Desktop). Controlla il report QC e i fotogrammi in `out/qc/`; se qualcosa non va, correggi da solo e rifai.
2. Scrivi `out/post.md` con caption (hook + 2 righe + CTA) e 3–5 hashtag, e **mostra la caption nella chat** pronta da copiare.
3. `python -m reel open pronti` e spiega come mandarlo sul telefono: WhatsApp Web a se stessi **come Documento**, poi sull'iPhone apri il file e "Salva video"; oppure iCloud.com → Foto → Carica (compare nel rullino). In Instagram/TikTok: scegli la copertina sul fotogramma con l'hook.

## Regole
- Mai più di 4 domande per volta; se l'utente scrive in modo vago, scegli tu l'opzione consigliata e dillo.
- Se qualcosa fallisce: spiega in una frase semplice ("non trovo la parola 'gratis' nel video, forse è stata tagliata") e proponi un'alternativa. Non mostrare tracce di errore.
- Lavori lunghi (trascrizione, render): avvisa prima quanto ci vorrà circa.
