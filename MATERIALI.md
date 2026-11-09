# Materiali: cosa ti serve e dove trovarlo

Tutto va nella cartella `assets/`. Dopo aver aggiunto file, di' a Claude **"aggiorna il catalogo"** (`python -m reel catalog`): crea `music_catalog.csv` e `sfx_catalog.csv`, dove puoi annotare licenza, fonte ed energia.

## 1. Musica → `assets/music/<mood>/`
Cartelle già pronte: `chill`, `energetica`, `epica`, `emozionale`, `corporate` (puoi crearne altre).
Fonti royalty-free:
| Fonte | Note sulla licenza |
|---|---|
| **Pixabay Music** (pixabay.com/music) | gratis, uso commerciale ok, senza attribuzione. Alcuni brani possono ricevere reclami Content ID: conserva la pagina del download |
| **YouTube Audio Library** (studio.youtube.com → Audio Library) | gratis; alcuni brani richiedono attribuzione (scrivila nel catalogo) |
| **Mixkit** (mixkit.co/free-stock-music) | gratis, licenza Mixkit |
| **Epidemic Sound / Artlist** | a pagamento, i più sicuri per i social e per i brand |

Consigli:
- Scarica **8–10 brani per mood** in MP3/WAV. Meglio strumentali (senza voce), così non coprono il parlato.
- Le canzoni di tendenza (trend audio) **non vanno messe nel montaggio**: aggiungile dall'app di IG/TikTok al momento della pubblicazione. In quel caso chiedi a Claude un export *senza musica*.
- Nel catalogo scrivi sempre `licenza` e `fonte` (link).

## 2. Effetti sonori → `assets/sfx/<categoria>/`
Ce ne sono già 9 di base generati (`python -m reel sfx-base`): pop, click, ding, boom, whoosh, glitch, typing.
Per una qualità migliore aggiungi i tuoi da: **Pixabay Sound Effects**, **Mixkit SFX**, **freesound.org** (controlla la licenza: preferisci CC0).
Lista consigliata (5 per tipo): whoosh/swoosh · pop/bubble · ding/notification · boom/bass drop/impact · click/mouse · typing/keyboard · camera shutter · cash register · riser · record scratch.

## 3. Font → `assets/fonts/`
Già inclusi (licenza OFL, gratis): **Montserrat** SemiBold, ExtraBold e Black, **Bebas Neue**.
Puoi aggiungerne altri da fonts.google.com (consigliati: *Anton*, *Poppins Black*, *Inter*). Poi cambia il nome del font in `config/caption_presets.yaml` o `config/brand.yaml`.

## 4. Immagini e grafiche → `assets/overlays/`
- **Logo** in PNG con sfondo trasparente (`logo.png`) → poi scrivi il percorso in `config/brand.yaml`
- Frecce, cerchi, icone, screenshot per i tutorial (PNG trasparenti). Fonti: flaticon.com, icons8.com (controlla l'attribuzione)
- **Emoji**: non servono, Claude le scarica da sole (Twemoji, licenza CC-BY 4.0: in caso di uso commerciale cita "Twemoji" nella bio o nella descrizione) con `--emoji 🔥`

## 5. Colore (facoltativo) → `assets/luts/`
File `.cube` per dare un "look" (es. caldo, cinematico). Molti LUT gratuiti si trovano online. Si applicano con: "applica il LUT caldo".

## 6. Identità del tuo profilo → `config/brand.yaml`
Decidi: 2–3 colori (es. giallo `#FFD400`, verde `#00E676`), il font per i titoli e il testo della tua CTA tipica ("Seguimi per altri trucchi").

## 7. Per girare (attrezzatura minima)
- Telefono in **verticale**, 1080p o 4K, **30 fps**, camera posteriore se possibile
- **Microfono lavalier** (a clip) wireless: è la cosa che migliora di più il risultato
- Luce frontale morbida (finestra davanti a te o ring light); sfondo ordinato
- Stanza silenziosa, senza eco (tende, tappeti, armadi aiutano)
- Lascia **1 secondo di silenzio** prima di iniziare e dopo aver finito; se sbagli, ripeti tutta la frase: Claude tiene l'ultima ripresa
