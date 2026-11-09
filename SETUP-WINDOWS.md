# Installazione su Windows (anche Boot Camp su Mac)

Tempo: circa 20 minuti. Serve una connessione internet. Fai i passi **in ordine**.

## 1. Apri PowerShell
Premi `Start`, scrivi **PowerShell**, clic su *Windows PowerShell*.
Incolla un comando alla volta (tasto destro = incolla) e premi Invio.

## 2. Installa i programmi di base
```powershell
winget install --id Git.Git -e
```
```powershell
winget install --id Python.Python.3.12 -e
```
```powershell
winget install --id Gyan.FFmpeg -e
```
```powershell
winget install --id OpenJS.NodeJS.LTS -e
```
(Node.js serve solo per le grafiche avanzate della fase 2: puoi saltarlo.)

**Chiudi e riapri PowerShell**, poi controlla:
```powershell
python --version
```
```powershell
ffmpeg -version
```
Se vedi i numeri di versione, è tutto ok.

## 3. Installa Claude Code
Più semplice: l'app **Claude desktop** (claude.ai/download), scheda *Code*.
Oppure da terminale:
```powershell
irm https://claude.ai/install.ps1 | iex
```

## 4. Scarica il progetto
```powershell
cd $HOME\Documents
```
```powershell
git clone <URL-DEL-TUO-REPO> reel-studio
```
```powershell
cd reel-studio
```

## 5. Ambiente Python del progetto
```powershell
python -m venv .venv
```
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
```powershell
.\.venv\Scripts\Activate.ps1
```
```powershell
pip install -r requirements.txt
```
Ogni volta che riapri PowerShell per lavorare: `cd $HOME\Documents\reel-studio` e poi `.\.venv\Scripts\Activate.ps1`.

## 6. Controllo finale
```powershell
python -m reel doctor
```
```powershell
python -m reel sfx-base
```
Tutte le righe devono essere `OK`. La **prima trascrizione** scarica il modello Whisper (circa 1,5 GB per `medium`): è normale che ci metta qualche minuto.

## 7. Avvia Claude nel progetto
```powershell
claude
```
(o apri la cartella `reel-studio` dall'app desktop) e scrivi: **"nuovo video prova"**.

---
### Note per Boot Camp / Mac Intel
- Non hai una GPU NVIDIA: la trascrizione gira sul processore. Con il modello `medium` un video di 1 minuto richiede circa 1–3 minuti. Per le prove veloci chiedi "trascrivi con modello small".
- Il render finale di un reel da 30 s richiede circa 1–2 minuti. L'anteprima è molto più veloce.
- Tieni i progetti sul disco Windows (non sulla partizione macOS): i percorsi funzionano meglio.

### Problemi comuni
| Problema | Soluzione |
|---|---|
| `ffmpeg` non riconosciuto | chiudi e riapri PowerShell; se persiste: `winget install Gyan.FFmpeg` |
| `Activate.ps1` bloccato | esegui il comando `Set-ExecutionPolicy` del punto 5 |
| Video dell'iPhone (HEVC/HDR) con colori strani | `ingest` lo normalizza in automatico; se serve forzalo con `--normalize` |
| Trascrizione lenta | usa il modello `small`; chiudi gli altri programmi |
