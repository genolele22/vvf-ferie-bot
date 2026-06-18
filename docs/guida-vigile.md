# Guida per il vigile — Chiedere le ferie con il bot Telegram

Questa guida spiega, passo per passo, come usare il bot delle ferie del Turno B.
Ti serve solo il telefono con **Telegram** installato.

---

## 1. A cosa serve il bot

Con il bot puoi:

- chiedere le ferie (uno o più turni);
- vedere a che punto sono le tue richieste;
- scambiare il tuo giorno di riposo (il "salto") con un collega;
- aggiornare la password della tua email.

Non devi più scrivere mail a mano né compilare moduli: fa tutto il bot.

---

## 2. La prima volta: registrarsi

La registrazione si fa **una volta sola**.

1. Apri la chat del bot su Telegram.
2. Scrivi `/start` e invia.
3. Il bot ti chiede l'**email** di lavoro (quella che finisce con `@vigilfuoco.it`).
   Scrivila e invia.
4. Il bot ti chiede la **password** della tua email `@vigilfuoco.it`.
   Scrivila e invia.

> **Attenzione alla password:** appena la invii, il bot **cancella da solo** il
> messaggio con la password, così nessuno la vede nella chat. È normale.

Se l'email e la password sono giuste, vedi il messaggio
**"Registrazione completata"** e compare il menu con i tasti. Sei pronto.

Se qualcosa non va:
- *"Email non trovata in anagrafica"* → hai sbagliato a scrivere l'email, oppure
  non sei ancora stato inserito. Riprova o avvisa il responsabile.
- *"Password non corretta"* → hai sbagliato la password della mail. Riprova con `/start`.

---

## 3. Il menu

Dopo la registrazione vedi quattro tasti in basso:

| Tasto | A cosa serve |
|---|---|
| 📅 **Richiedi ferie** | Chiedere le ferie |
| 📋 **Le mie richieste** | Vedere e annullare le tue richieste |
| 🔄 **Scambia salto** | Scambiare il riposo con un collega |
| 🔑 **Aggiorna password** | Cambiare la password della tua email |

Se i tasti non compaiono, scrivi `/start`.

---

## 4. Chiedere le ferie

1. Premi **📅 Richiedi ferie**.
2. Scegli il **mese** che ti interessa (puoi scegliere tra questo mese e i 5 successivi).
3. Compaiono i turni del Turno B di quel mese. Ogni turno ha:
   - ☀️ = **diurno** (08:00 → 20:00)
   - 🌙 = **notturno** (20:00 → 08:00)
4. **Tocca** i turni che vuoi chiedere. Quando ne tocchi uno compare la spunta ✅.
   Toccandolo di nuovo lo togli.
5. Puoi sceglierne **quanti vuoi**, anche di giorni diversi.
6. Quando hai finito premi **Conferma**.

Il bot ti mostra l'elenco delle richieste inviate (ognuna con un numero, es. `#123`)
e invia in automatico una **mail alla fureria**.

> **La risposta arriva via email.** La fureria ti dirà via mail (e con un messaggio
> del bot) se le ferie sono accettate o no. È normale che per qualche giorno la
> richiesta resti **"in attesa"**.

Tasti utili durante la scelta:
- **⬅️ Cambia mese** → torni a scegliere un altro mese.
- **✖️ Annulla** → chiudi tutto senza inviare niente.

---

## 5. Vedere e annullare le richieste

Premi **📋 Le mie richieste**. Vedi l'elenco con lo stato di ognuna:

- ⏳ / "in attesa" → la fureria non ha ancora risposto;
- ✅ / "accettata" → ferie concessa;
- ❌ / "rifiutata" → ferie non concessa (a volte con il motivo scritto sotto).

**Annullare una richiesta:** sotto l'elenco compare un tasto
**❌ Annulla** per ogni richiesta ancora *in attesa*. Premilo per ritirarla.
Le richieste già accettate o rifiutate non si annullano da qui: parla con la fureria.

---

## 6. Scambiare il salto (riposo) con un collega

Il "salto" è il tuo giorno di **riposo compensativo**. Con questa funzione lo puoi
scambiare con il riposo di un altro vigile dello stesso blocco di turni.

1. Premi **🔄 Scambia salto**.
2. Il bot ti mostra qual è il **tuo prossimo riposo**.
3. Scegli il **salto** (es. *B3*) con cui vuoi scambiare.
4. Scegli il **collega** preciso nell'elenco.
5. Controlla il riepilogo (tu cedi il tuo riposo, lui cede il suo) e premi **✅ Proponi**.

Da qui in poi:

- Al collega arriva la tua proposta: lui deve premere **✅ Confermo**.
- Dopo la sua conferma, la **fureria** deve approvare lo scambio.
- Quando tutto è approvato, **a te e al collega** arriva un messaggio di conferma
  con i nuovi giorni di riposo. Riceverete anche una mail.

Se il collega rifiuta, o se la fureria non approva, ti arriva un messaggio che te lo dice.
In qualsiasi momento prima di proporre puoi premere **✖️ Annulla**.

---

## 7. Cambiare la password dell'email

Se cambi la password della tua email `@vigilfuoco.it`, devi aggiornarla anche nel bot,
altrimenti le mail non partono.

1. Premi **🔑 Aggiorna password**.
2. Scrivi la nuova password (il bot la cancella subito dalla chat).
3. Se è giusta, vedi **"Password aggiornata"**.

---

## 8. Problemi comuni

- **Non vedo i tasti del menu** → scrivi `/start`.
- **Il bot dice che non sono registrato** → fai la registrazione con `/start` (punto 2).
- **"Email non inviata"** dopo aver chiesto le ferie → la password della mail è
  sbagliata o scaduta: aggiornala con **🔑 Aggiorna password**.
- **Mi sono bloccato a metà di un'operazione** → scrivi `/start`: ricominci da capo
  senza problemi.
- **Ho sbagliato richiesta** → vai su **📋 Le mie richieste** e annulla quella in attesa.

In caso di dubbi, contatta la fureria.
