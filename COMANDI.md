# Cosa dire a Claude: cheat-sheet

Parla in modo naturale: queste sono solo frasi d'esempio. Per i tempi puoi usare i **secondi** ("a 0:12") oppure, meglio, le **parole** ("quando dico *gratis*"): così il testo resta sincronizzato anche se poi tagli altro.
Tra parentesi c'è il comando che Claude esegue (`python -m reel ...`). Non devi impararlo.

## 🗂️ Progetto
| Dici | Cosa succede |
|---|---|
| "nuovo video **ricette-veloci**" | crea `projects/ricette-veloci/` con la scaletta (`new`) |
| "ho messo i file, importali" | legge i video, sistema VFR/HDR dell'iPhone (`ingest`) |
| "trascrivi" / "trascrivi con modello small" | trascrizione parola per parola (`transcribe`) |
| "fammi vedere il montaggio" | elenco dei pezzi con il testo detto (`show`) |
| "annulla" | torna indietro di una modifica (`undo`) |

## ✂️ Tagli
| Dici | Comando |
|---|---|
| "taglia i silenzi" (leggero / normale / aggressivo) | `autocut --level normale` |
| "togli gli ehm" / "lascia gli ehm" | incluso in `autocut` / `--keep-fillers` |
| "elimina la frase *allora come dicevo*" | `cut --phrase "allora come dicevo"` |
| "ho sbagliato all'inizio, tieni solo l'ultima ripresa di *oggi vi mostro*" | Claude trova le ripetizioni e taglia le prime (`find` + `cut --phrase --n`) |
| "taglia da 0:12.4 a 0:15" | `cut --from 0:12.4 --to 0:15` |
| "accorcia l'inizio del pezzo 3 di mezzo secondo" | `trim 3 --head 0.5` |
| "sposta il pezzo *ecco il risultato* all'inizio" (hook) | `move` |
| "portalo sotto i 30 secondi" | Claude propone cosa togliere e chiede conferma |

## 🔍 Zoom e inquadratura
| Dici | Comando |
|---|---|
| "jump cut con zoom alternati" | `autozoom` (punch-in 112% a pezzi alterni) |
| "zoom forte quando dico *attenzione*" | `zoom --from "parola:attenzione" --to "fine:attenzione" --factor 1.3` |
| "zoom 120% da 0:10 a 0:13" | `zoom --from 0:10 --to 0:13 --factor 1.2` |
| "nel video orizzontale tieni il viso più in alto" | `zoom ... --focus-y 0.3` |

## 💬 Sottotitoli
| Dici | Comando |
|---|---|
| "sottotitoli stile **bold**" (parola evidenziata, gialla) | `captions --preset bold` |
| "stile **clean**" (frase con riquadro, sobrio) | `captions --preset clean` |
| "stile **pop**" (1–2 parole che esplodono) | `captions --preset pop` |
| "evidenzia *gratis* e *soldi*" | `captions --highlight gratis soldi` |
| "correggi *chatgpt* in *ChatGPT*" | `captions --replace "chatgpt=ChatGPT"` (meglio: aggiungilo a `config/glossario.txt` prima di trascrivere) |
| "metti 🔥 sotto *fuoco*" | `captions --emoji "fuoco=🔥"` |
| "togli i sottotitoli" | `captions --off` |

## 🅰️ Testi a schermo (sincronizzati)
Stili: `hook` (grande in alto), `title`, `cta` (riquadro giallo), `label` (etichetta), `number` (numero gigante "1", "2"...).
| Dici | Comando |
|---|---|
| "hook all'inizio: *3 errori che fai su Instagram* per 3 secondi" | `text "3 errori..." --at 0 --dur 3 --style hook` |
| "scrivi *ERRORE 1* quando dico *primo*" | `text "ERRORE 1" --at "parola:primo" --style title` |
| "numero 2 gigante quando dico *secondo*" | `text "2" --at "parola:secondo" --style number --dur 1.2` |
| "CTA finale *Seguimi per la parte 2* negli ultimi 3 secondi" | `text "..." --at -3 --end -0 --style cta` |
| "effetto macchina da scrivere" / "che entri da sotto" | `--anim typewriter` / `--anim slide` |

## ✨ Pop-up e grafiche
| Dici | Comando |
|---|---|
| "emoji 🤯 quando dico *incredibile*" | `popup --emoji 🤯 --at "parola:incredibile" --sfx sfx/pop/pop_1.wav` |
| "mostra lo screenshot *app.png* da 0:08 a 0:11" | `popup --image assets/overlays/app.png --at 0:08 --dur 3 --width 900 --y center` |
| "freccia che entra da destra a 0:20" | `popup --image assets/overlays/freccia.png --at 0:20 --anim slide` |
| "barra di avanzamento in alto" | `progress on` |
| "togli il secondo pop-up" | `remove popups 1` |

## 🔊 Audio
| Dici | Comando |
|---|---|
| "musica chill al 15%, che si abbassa quando parlo" | `music assets/music/chill/brano.mp3 --volume 0.15` (ducking automatico) |
| "fai partire il brano dal ritornello (secondo 42)" | `music ... --start 42` |
| "senza musica, la metto da TikTok" | `music --off` |
| "boom sul hook" | `sfx sfx/boom/boom_1.wav --at 0` |
| "ding quando dico *salva*" | `sfx sfx/ding/ding_1.wav --at "parola:salva"` |
| "pulisci la voce" | attivo di default: denoise + EQ + compressore + -14 LUFS |

## 🎞️ Transizioni (con misura!)
| Dici | Comando |
|---|---|
| "flash bianco e whoosh quando cambio argomento (*secondo punto*)" | `transition --type flash --at "parola:secondo" --sfx sfx/whoosh/whoosh_1.wav` |
| "whoosh su tutti i tagli" | `transition --type none --all-cuts --sfx sfx/whoosh/whoosh_2.wav` |
| "dissolvenza al nero" | `transition --type dip --at ...` |

## 📤 Esportazione
| Dici | Comando |
|---|---|
| "fammi un'anteprima" | `preview` → `out/preview.mp4` (540p, veloce) |
| "render finale" | `render` → `out/final.mp4` + controllo qualità + fotogrammi in `out/qc/` |
| "esporta anche senza sottotitoli/musica" | Claude crea la variante (`render --name senza_sub.mp4`) |
| "scrivimi caption e hashtag" | testo del post dalla trascrizione |

---
### Una sessione tipo (copia e incolla)
1. `nuovo video trucchi-canva`
2. *(copi i video in `projects/trucchi-canva/raw/`)* → `importa e trascrivi`
3. `taglia silenzi normale, togli gli ehm, tieni solo le ultime riprese delle frasi ripetute`
4. `jump cut con zoom alternati, sottotitoli bold, evidenzia le parole chiave`
5. `hook "3 trucchi Canva che nessuno usa" per 3s con boom; numero 1/2/3 quando li dico; CTA finale "Seguimi per la parte 2"`
6. `musica energetica al 12%, pop sui pop-up` → `anteprima`
7. *(correzioni)* → `render finale` → `caption e hashtag`
