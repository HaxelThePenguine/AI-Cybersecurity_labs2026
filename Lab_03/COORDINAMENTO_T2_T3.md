# Lab 3 - Coordinamento Task 2 / Task 3

Regole per lavorare in parallelo senza sovrapporci né creare conflitti git. Questo file non è nel repo (è in `.gitignore`).

## Chi fa cosa

| Chi | Task | Contenuto |
| --- | --- | --- |
| Collega | Task 2 - One-Class SVM | 2A (solo normal, `nu` vs 0.5), 2B (contaminazione 0/10/20/50/100% + caso unknown), 2C (test) |
| Marco | Task 3 - LOF | 4 valori di `n_neighbors`, criterio di scelta, fit finale e valutazione sul test |

## File di proprietà esclusiva

- **Collega → `Lab_03/lab3.ipynb`.** Aggiunge le sezioni del Task 2 dopo l'ultima cella del Task 1 (cella 14). Marco non modifica questo notebook finché non si fa il merge finale.
- **Marco → `Lab_03/lab3_task3.ipynb`** (nuovo). Contiene una copia delle celle di setup e preprocessing di `lab3.ipynb` (import/seed, caricamento dati, preprocessor) seguita dal Task 3. Il collega non lo modifica.
- **Celle del Task 1:** nessuno le modifica. Se serve cambiare il preprocessing (feature, scaling, encoding) lo si concorda prima, perché cambia i risultati di entrambi.

## File condivisi: regole

### `LOGBOOK.md`
- Run **1-7 → Task 2** (collega). Run **8-9 → Task 3** (Marco). Se il Task 2 usa meno di 7 run, i numeri restanti si rinumerano solo al merge finale.
- Ognuno aggiunge/modifica **solo le proprie righe**. La riga `| 1 | 2 | | ...` vuota la sostituisce il collega.
- La riga **Count** in fondo la aggiorna solo chi fa il merge finale.
- Ipotesi scritte **prima** di eseguire la run, non riscritte dopo (regola del PDF).

### `NOTES.md`
- Ognuno scrive **solo sotto la propria sezione** (`## Task 2 ...` / `## Task 3 ...`).
- Non si toccano: riga **Status**, sezioni Task 1, tabella **Final comparison**, checklist di consegna. Si aggiornano al merge finale.

## Workflow git

1. `git pull --rebase` prima di iniziare a lavorare e prima di ogni push.
2. Commit piccoli che toccano **solo i propri file / le proprie sezioni**.
3. Messaggio con prefisso: `Task 2: ...` oppure `Task 3: ...`.
4. In caso di conflitto su `LOGBOOK.md` o `NOTES.md`: tenere entrambe le modifiche (sono in righe/sezioni diverse). Su un `.ipynb` non si risolve a mano: ci si sente prima.

## Convenzioni comuni (devono coincidere per confrontare i risultati)

- Seed **42** (`random`, `numpy`, `torch` come nella cella di setup).
- Preprocessing del Task 1 **fittato solo sul train** (106 feature: 35 numeriche + 71 one-hot).
- Labels usate **solo** per costruire i subset e per valutare, mai come segnale di training.
- Test set **solo dove il PDF lo chiede** (2C per il Task 2, valutazione finale per il Task 3). Eventuale validation ricavata da `Lab3_train.csv`.
- Metrica principale: **macro-F1 binaria** (normal vs anomaly), più confusion matrix e **recall per tipo di attacco** (dos, probe, r2l).
- Convenzione predizioni: anomalia = 1. Attenzione: sklearn (OC-SVM, LOF) restituisce **-1 = outlier, +1 = inlier** → convertire con `(pred == -1).astype(int)`.
- Tempi di training misurati e riportati nel logbook (colonna "Time s").

## Merge finale

1. Il Task 2 si chiude e viene pushato per primo.
2. Marco fa `git pull`, incolla le sezioni del Task 3 in `lab3.ipynb` dopo il Task 2 (senza duplicare setup/preprocessing).
3. Si riesegue **tutto il notebook dall'inizio** e si controlla che i numeri coincidano con logbook e NOTES.
4. Si elimina `lab3_task3.ipynb`, si aggiornano Count, Status e si fa push.
