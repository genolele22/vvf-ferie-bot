# Scambio salto turno tra vigili — design

> Stato: **IMPLEMENTATO** su branch `scambio-salto` (commit `a5caf78`), pushato su origin.
> Non ancora mergiato su `main` né deployato su Fly.
> Nodo TiDB/AUTO_INCREMENT: risolto — le tabelle nuove (`bot_scambi_salto`, `salto_override`)
> usano id espliciti via `_next_id()` (`MAX(id)+1`), non passano da `insert_salto`/`bot_salto`.

## Cos'è il problema

Il **salto turno** è un **riposo compensativo** da contratto. Tutti i vigili del turno B
lavorano gli stessi giorni; a rotazione ogni giorno-turno è etichettato con uno slot
**B1…B8**. Quando arriva il giorno col proprio slot, il vigile prende il salto turno = **riposa**.

Capita che due vigili (es. titolari slot B4 e B6) vogliano **scambiarsi il giorno di riposo**.

### Vincolo contrattuale
Lo scambio può avvenire **solo dentro lo stesso blocco ciclico B1→B8**.
Esempio: se oggi è B5, posso scambiare con B6, B7, B8 — **non** con un B2 che ricade nel
giro successivo. Il limite alto è sempre **B8** (fine giro). Solo in avanti, mai su giorni passati.

### Caratteristiche
- Il riposo compensativo copre **sempre D + N insieme** (giorno diurno + notturno dello slot).
- Vale per **tutto il turno B** (qualsiasi vigile può scambiare con qualsiasi altro, stesso blocco).

## Modello dati esistente (per riferimento)

- `vigili.salto_id` → FK a `salti_turno` (codici B1…B8): lo **slot di riposo** assegnato al vigile.
- `salti_turno` (id, codice): 8 righe B1…B8.
- `bot_salto` (vigile_id, data, tipo ENUM('D','N')): le **date concrete** di riposo registrate.
  Funzioni in `database.py`: `insert_salto`, `get_salti_utente`, `is_salto`.
- `calendario.json` (`data/`): per ogni data `{tipo: D|N, gruppo: B#}`.
  Sequenza ciclica reale (da gen 2025): **B3→B4→B5→B6→B7→B8→B1→B2→(ricomincia)**.
  Ogni slot occupa 2 giorni: un D e il N del giorno dopo (es. B5 = 10-gen D, 11-gen N).
- `calendar_turni.py`: lettura calendario (`get_turno`, `date_in_servizio`, ...).

### Note tecniche scoperte
- `database.py` del bot usa **una sola connessione** (`get_conn`), in prod punta a TiDB (SSL).
  **Nessun dual-write lato Python** — il dual-write su TiDB è del gestionale PHP.
- ⚠️ **DA VERIFICARE su DB live prima di implementare:** `bot_salto` è dichiarata con
  `AUTO_INCREMENT` e `insert_salto` fa `INSERT IGNORE` **senza id**. Ma la memoria di progetto
  segnala che su TiDB *non c'è AUTO_INCREMENT implicito* e *`INSERT IGNORE` senza id fallisce
  silenziosamente*. Contraddizione non risolta: o la nota è superata, o `insert_salto` ha un
  bug latente. **Per sicurezza la nuova tabella NON si affida ad AUTO_INCREMENT**: l'INSERT
  calcola l'id con `SELECT COALESCE(MAX(id),0)+1` e lo passa esplicito (pattern usato altrove
  per TiDB). Verificare il comportamento reale di `bot_salto` quando si implementa.

## Soluzione scelta: tabella a parte + sync con `bot_salto`

`bot_salto` resta la **verità** sui riposi effettivi (tutto il resto — calendario, fogli, ODT —
continua a leggerla senza modifiche). La nuova tabella è **workflow + storico/audit**.
Solo all'**approvazione** si scrive su `bot_salto`.

### Tabella `bot_scambi_salto`

> Nota: `AUTO_INCREMENT` lasciato nel DDL per compatibilità MySQL locale, ma **l'INSERT passa
> l'id esplicito** (`SELECT COALESCE(MAX(id),0)+1`) per sicurezza su TiDB — vedi note tecniche.

```sql
CREATE TABLE IF NOT EXISTS bot_scambi_salto (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  vigile_a_id     INT UNSIGNED NOT NULL,   -- chi propone (es. B4)
  vigile_b_id     INT UNSIGNED NOT NULL,   -- controparte (es. B6)
  blocco_inizio   DATE NOT NULL,           -- inizio del giro B1→B8
  blocco_fine     DATE NOT NULL,           -- fine del giro (B8)
  data_a_d        DATE NOT NULL,           -- salto originale di A: giorno diurno
  data_a_n        DATE NOT NULL,           -- salto originale di A: giorno notturno
  data_b_d        DATE NOT NULL,           -- salto originale di B: giorno diurno
  data_b_n        DATE NOT NULL,           -- salto originale di B: giorno notturno
  stato           ENUM('proposto','confermato','approvato','rifiutato','annullato')
                    NOT NULL DEFAULT 'proposto',
  creato_da       INT UNSIGNED NOT NULL,
  approvato_da    INT UNSIGNED DEFAULT NULL,
  creato_il       DATETIME DEFAULT CURRENT_TIMESTAMP,
  modificato_il   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT bot_scambi_salto_ibfk_1 FOREIGN KEY (vigile_a_id) REFERENCES vigili (id),
  CONSTRAINT bot_scambi_salto_ibfk_2 FOREIGN KEY (vigile_b_id) REFERENCES vigili (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Effetto sullo stato `approvato` (transazione su `bot_salto`)
- A: rimuovo le righe (`data_a_d`/D, `data_a_n`/N) → inserisco (`data_b_d`/D, `data_b_n`/N)
- B: inverso.
- Se lo scambio viene **annullato**: ripristino le righe originali (sono salvate nello scambio).

### Workflow
```
B4 propone scambio con B6   → stato: proposto    (notifica a B6)
B6 conferma                 → stato: confermato  (notifica fureria)
Fureria approva             → stato: approvato    → scrive su bot_salto
```
Rifiuto / annullo possibili fino all'approvazione.

### UX proposta (decisa)
- B4 sceglie **il vigile** (lista turno B); il sistema **trova da solo** il salto di quel
  vigile nel blocco corrente. Poi mostra a B4 il salto trovato e chiede conferma.

## Piano implementazione (passo passo)

**Branch:** `scambio-salto`. Niente push/deploy finché Lele non testa.

1. **`database.py`**
   - `CREATE TABLE IF NOT EXISTS bot_scambi_salto` nell'init (stile `bot_salto`).
   - `blocco_corrente(data)` → `(inizio_B1, fine_B8)` del giro corrente.
   - `salto_vigile_nel_blocco(vigile_id, blocco)` → date D+N di salto del vigile nel blocco.
   - `lista_vigili_turno_b()` → per scegliere la controparte.
   - `crea_scambio`, `conferma_scambio`, `approva_scambio` (scrive su `bot_salto` in transazione),
     `rifiuta_scambio`, `annulla_scambio`.
   - `scambi_per_stato(...)` per menu/notifiche.

2. **`calendar_turni.py`**
   - helper confini blocco B1→B8 e mappa `data → slot B#`.

3. **`handlers/`**
   - flusso Telegram: «Proponi scambio salto» → scegli vigile → conferma → notifica B6 →
     conferma → notifica fureria → approva. Notifica al prossimo attore ad ogni passaggio.

4. **dump SQL** (`database vvf sql.sql`) — aggiungere la tabella allo schema documentato.

## Punto aperto da rifinire in implementazione
**Confine esatto del blocco.** Cronologicamente la sequenza parte da B3, non da B1, quindi
"inizio/fine giro" va ancorato a un esempio concreto del calendario per non sbagliare di un
turno. Verificare col `calendario.json` reale e far confermare a Lele prima di chiudere
`blocco_corrente()`.
