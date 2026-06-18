# Guida per il furiere — Bot Telegram + Gestionale web

Il furiere usa **due strumenti** che lavorano insieme:

| Strumento | Dove | A cosa serve |
|---|---|---|
| **Bot Telegram** | Sul telefono | Ricevere le richieste e gli avvisi, approvare gli scambi salto |
| **Gestionale web** | Nel browser (computer) | Compilare il foglio di servizio, accettare/respingere le ferie, scaricare l'ODT |

Regola semplice da ricordare:
- **Le richieste arrivano dal bot.**
- **Il lavoro vero (foglio e ferie) si fa nel gestionale.**

---

# PARTE 1 — Il bot Telegram

## 1.1 Registrazione

Come tutti i vigili, la prima volta scrivi `/start` e inserisci la tua email
`@vigilfuoco.it` e la password della mail. Vedi la *Guida per il vigile* per i dettagli.

> Il tuo telefono deve essere riconosciuto come **fureria**: in quel caso ricevi anche
> gli avvisi e i tasti per approvare. Se non li ricevi, avvisa chi gestisce il bot.

Anche tu, come furiere, hai gli stessi quattro tasti del vigile
(📅 Richiedi ferie, 📋 Le mie richieste, 🔄 Scambia salto, 🔑 Aggiorna password):
servono per le **tue** ferie personali.

## 1.2 Cosa ti arriva sul bot

Sul bot ti arrivano in automatico:

1. **Nuove richieste di ferie** — quando un vigile chiede le ferie, ti arriva un
   messaggio con nome, gruppo e i turni richiesti. *La richiesta la gestisci poi
   nel gestionale* (vedi Parte 2). Il vigile riceve la risposta via mail.

2. **Scambi salto da approvare** — quando due vigili si sono messi d'accordo per
   scambiare il riposo, ti arriva il messaggio **"🔄 Scambio salto da approvare"**.

## 1.3 Approvare uno scambio salto (dal bot)

Quando arriva un messaggio **"Scambio salto da approvare"**, hai due tasti:

- **✅ Approva** → lo scambio diventa valido. Il sistema aggiorna da solo i fogli
  di servizio interessati e manda la mail di conferma a tutti e due i vigili.
- **✖️ Rifiuta** → lo scambio salta e i due vigili vengono avvisati.

Dopo aver approvato, compare anche il tasto **↩️ Annulla scambio**: serve se hai
approvato per errore. Te lo chiede una seconda volta per sicurezza; se confermi,
i due vigili tornano alla situazione di partenza.

> Se il sistema dice che **non può approvare per un conflitto**, vuol dire che uno dei
> due riposi è già coinvolto in un altro scambio. Annulla prima quello, poi riprova.

## 1.4 L'agenda delle ferie in CSV (facoltativo)

Se ti serve un riepilogo delle ferie da aprire in Excel:

1. Scrivi `/agenda` nella chat.
2. Scrivi il periodo, in uno di questi modi:
   - `05/2026` → tutto il mese di maggio 2026;
   - `01/05/2026-31/05/2026` → un intervallo di date;
   - `18/06/2026` → un solo giorno.
3. Il bot ti manda un file CSV con tutte le richieste di quel periodo.

---

# PARTE 2 — Il gestionale web

## 2.1 Come si apre

Apri il browser (Chrome) e vai all'indirizzo:

> **https://vvf-gestionale.fly.dev/**

In alto trovi la barra dei menu:

| Menu | A cosa serve |
|---|---|
| 🏠 **Cruscotto** | Il calendario del mese |
| 📋 **Nuovo Foglio / Foglio** | Compilare il foglio di servizio |
| 👥 **Personale** | L'anagrafica dei vigili |
| 🗓️ **Agenda** | Accettare o respingere le richieste di ferie |

> I menu **📊 Reportistica**, **⚙️ Amministrazione** e **🚪 Esci** non sono ancora
> attivi: per ora ignorali. Il menu **📓 Logbook** è solo per i collaudi (segnalare
> bug e richieste).

## 2.2 Il Cruscotto (calendario)

È la pagina iniziale. Mostra il calendario del mese. I turni del **Turno B** sono
caselle colorate e **cliccabili**:

- 🌅 giallo = diurno (08:00→20:00);
- 🌙 azzurro = notturno (20:00→08:00);
- ✅ verde = foglio **già compilato**.

Clicca sulla casella di un turno per aprire (o creare) il suo foglio di servizio.
Usa le frecce **◀ Prec.** e **Succ. ▶** per cambiare mese.

## 2.3 L'Agenda — accettare o respingere le ferie

Apri **🗓️ Agenda**. Vedi tutte le richieste di ferie del mese, raggruppate per vigile
e periodo. Per ogni turno ci sono due spunte:

- **accetto** (verde) → la ferie viene concessa e finisce sul foglio;
- **respingo** (rosso) → la ferie viene rifiutata e tolta dal foglio.

Caratteristiche:

- La scelta è **immediata**: tocchi la spunta e si salva da sola, non c'è un tasto "salva".
- Puoi sempre **cambiare idea**: ri-tocca l'altra spunta, o togli la spunta per
  rimetterla "in attesa".
- Per un intero periodo puoi usare **✓ tutti** o **✗ tutti**.
- In cima alla pagina vedi anche gli **scambi salto approvati** del mese.

> **Importante:** accettare in Agenda **concede** la ferie e la mette sul foglio, ma
> **non avvisa ancora il vigile**. L'avviso al vigile (Telegram + mail) parte dopo,
> quando **scarichi l'ODT** di quel turno (vedi 2.5). Questo serve perché di solito il
> foglio si stampa poco prima del servizio.

## 2.4 Il Foglio di servizio

Apri un foglio dal Cruscotto (clic sulla casella del turno) oppure dal menu **📋 Foglio**.

**In alto (intestazione):**
- **Capo Servizio** e **Vice Capo Servizio**: scegli dalla tendina **oppure**
  trascina un vigile nella casella.
- **Funzionario** e **Note generali**: campi liberi.
- **💾 Salva** salva l'intestazione.

**Comporre il foglio (al centro):**
- A destra c'è l'elenco dei vigili disponibili. **Trascina** un vigile nella posizione
  (squadra/mezzo) dove deve andare.
- Ogni posizione ha un **numero massimo di posti** uguale al modulo ufficiale: oltre
  quel numero non te ne fa aggiungere.
- Per **togliere** un vigile da una posizione, usa la ✕ sulla sua casella.
- C'è una **casella di ricerca** ("Trova vigile nel foglio…") per trovare subito un
  cognome in tutto il foglio.

**Riquadri speciali (a sinistra):**
- **🚫 Ferie respinte**: vigili a cui hai respinto la ferie. Se ti accorgi che invece
  deve andare in ferie, **trascinalo** nella colonna ferie: la richiesta torna accettata.
- **🏛️ Ferie d'ufficio**: per mettere in ferie un vigile **senza** che ci sia una
  richiesta dal bot (decisione d'ufficio). Trascini il vigile nel riquadro.

**Salto e scambi:**
- Il foglio mostra chi è **in salto** (riposo compensativo).
- Con **🔄 Cambia salto…** puoi gestire lo scambio del salto direttamente dal web,
  senza passare dal bot.

**Barra dei tasti in alto:**

| Tasto | Cosa fa |
|---|---|
| 🔒 / 🔓 | Blocca/sblocca il foglio. **Bloccato = nessuno può modificarlo** (utile quando è definitivo) |
| 💾 **Salva** | Salva l'intestazione |
| 🖨️ **Stampa** | Apre l'anteprima di stampa |
| 🕑 **Servizio precedente** | Apre la stampa del turno precedente, per confronto |
| 📄 **Scarica .odt** | Scarica il documento ufficiale (vedi 2.5) |
| ↺ **Reset servizio** | Ricostruisce il foglio da zero (vedi 2.6) |

## 2.5 Scaricare l'ODT (importante!)

Il tasto **📄 Scarica .odt** scarica il foglio di servizio nel formato ufficiale
(si apre con LibreOffice / Word).

**Attenzione:** se su quel turno ci sono ferie ancora "in attesa", scaricando l'ODT:

1. quelle ferie vengono **approvate** in automatico;
2. ai vigili interessati parte la **notifica** (Telegram + mail).

Per questo, prima di scaricare, il sistema te lo chiede con un avviso
(**"Genera ODT e approva ferie"**). Premi **📄 Genera e approva** solo quando il
foglio è quello buono. È il momento in cui il vigile viene avvisato ufficialmente.

## 2.6 Reset servizio

Il tasto **↺ Reset servizio** **cancella tutte le assegnazioni e le ricostruisce da
zero** dal personale di turno.

- I **salti** e le **ferie/assenze restano**: non si perdono.
- Si perde invece ogni sistemazione fatta a mano (chi avevi spostato dove).

Usalo quando il foglio è confuso o vuoi ripartire pulito. Ti chiede conferma prima di farlo.

## 2.7 Il Personale

Il menu **👥 Personale** mostra l'anagrafica dei vigili. Da qui si controllano e
modificano i dati (qualifica, sede, patenti…).

---

# PARTE 3 — Il giro completo di una giornata (esempio)

1. Durante il mese arrivano sul **bot** le richieste di ferie dei vigili.
2. Apri il **gestionale → 🗓️ Agenda** e per ogni richiesta scegli **accetto** o **respingo**.
3. Quando arriva il momento di preparare il servizio, apri il **foglio** di quel turno
   (dal Cruscotto).
4. Sistemi i vigili nelle posizioni (trascinandoli), imposti Capo e Vice, controlli salti
   e ferie.
5. Quando il foglio è pronto, premi **📄 Scarica .odt**: le ferie in attesa di quel
   turno vengono approvate e i vigili **avvisati** (Telegram + mail).
6. Se nel frattempo due vigili hanno chiesto uno **scambio salto**, ti arriva l'avviso
   sul **bot**: premi **✅ Approva**.

---

# PARTE 4 — Problemi comuni

- **Non riesco a modificare il foglio** → controlla se è **bloccato** (🔒). Premi il
  lucchetto per sbloccarlo.
- **Ho approvato uno scambio per errore** → usa **↩️ Annulla scambio** sul messaggio del bot.
- **Il sistema non approva lo scambio (conflitto)** → uno dei riposi è già in un altro
  scambio: annulla quello prima.
- **Il foglio esce su troppe pagine** → fai un **↺ Reset servizio**: rimette tutto nei
  posti giusti rispettando il numero massimo per posizione.
- **Ho respinto una ferie per sbaglio** → trovi il vigile in **🚫 Ferie respinte** sul
  foglio: trascinalo nella colonna ferie e torna accettata.
- **Una ferie risulta "accettata" ma il vigile dice di non aver ricevuto niente** →
  è normale finché non scarichi l'ODT di quel turno: l'avviso parte allo scarico ODT.
