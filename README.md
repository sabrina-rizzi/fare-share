<div align="center">
  <img src="icon-192.png" width="88" height="88" alt="Logo Fare Share">
  <h1>Fare Share</h1>
  <p><em>Costo tragitto condiviso — PWA per calcolare e dividere il costo di uno spostamento in auto.</em></p>
</div>

---

> **Perché "Fare Share"?** Gioco di parole: *fare* in inglese è il **costo del viaggio**,
> e si legge come *"fair share"*, la **giusta parte** che ognuno deve pagare. In due parole:
> dividere il costo del tragitto in modo equo.

**Fare Share** è una web app installabile (PWA) che calcola quanto costa un
tragitto in auto — carburante, extra dovuto al traffico, spese accessorie — e ripartisce
la spesa tra le persone che lo condividono. Funziona **offline**, **senza account**,
**senza backend** e **senza API a pagamento**: tutti i dati restano sul dispositivo.

È scritta in **HTML, CSS e JavaScript vanilla** in un unico file, senza framework né build step.

## Funzionalità principali

- **Calcolo del costo** per veicoli a **benzina/diesel** (km/l + €/l) o **elettrici** (kWh/100km + €/kWh), con extra-costo per i minuti di coda.
- **Modalità di percorso** flessibili: solo andata, andata/ritorno sullo stesso percorso, oppure andata e ritorno su percorsi diversi.
- **Distanza reale dagli indirizzi** con geocodifica **Nominatim** e calcolo percorso **OSRM**, tappe intermedie e mappa **Leaflet**.
- **Geolocalizzazione** (API nativa del browser) con reverse geocoding per compilare l'indirizzo di partenza.
- **Multi-tragitto**: profili salvati automaticamente in `localStorage` (crea, rinomina, duplica, elimina), con export/import `.json` per backup e condivisione.
- **N persone** con divisione **a percentuale fissa** o **proporzionale ai giorni percorsi**, **spese extra** (pedaggi, parcheggio, usura €/km) e **saldo "chi deve a chi"** in stile Splitwise semplificato.
- **Storico e report**: registrazione dei tragitti, grafico dell'andamento (SVG nativo, nessuna libreria), report mensile/annuale esportabile.
- **Stima CO₂ risparmiata** condividendo l'auto e **confronto con il trasporto pubblico**.
- **Nota spese stampabile / PDF** tramite foglio di stile dedicato e `window.print()`.
- **Prezzo carburante** precompilabile dall'**Osservatorio Prezzi Carburanti del MIMIT** (con override manuale sempre prioritario e degradazione pulita se il servizio non è raggiungibile).

## Stack tecnico

| Area | Scelta |
|------|--------|
| Frontend | HTML + CSS + JavaScript vanilla (single file, no build) |
| Mappe | [Leaflet](https://leafletjs.com/) |
| Geocodifica / percorsi | [Nominatim](https://nominatim.org/) + [OSRM](http://project-osrm.org/) (OpenStreetMap) |
| Prezzi carburante | [Open data MIMIT](https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti) |
| Offline / installabilità | Service Worker + Web App Manifest |
| Persistenza | `localStorage` (nessun backend) |

## Architettura in breve

- **Offline-first**: il service worker mette in cache l'app shell e le librerie statiche (Leaflet) con strategia *cache-first*, mentre i servizi che richiedono dati aggiornati (geocodifica, percorsi, tile mappa, prezzi) usano *network-first* con fallback pulito quando si è offline.
- **Stato unico**: ogni tragitto è un oggetto (veicolo, percorso, persone, spese, saldo, ecc.) versionato e serializzato in `localStorage`, con migrazione automatica dai vecchi salvataggi.
- **Zero dipendenze pesanti**: grafici e PDF sono realizzati con SVG nativo e `@media print`, per non compromettere l'uso offline.

## Come usarla in locale

Serve un piccolo server statico (il service worker non funziona da `file://`):

```bash
# dalla cartella del progetto
python -m http.server 8000
# poi apri http://localhost:8000
```

## Privacy

L'app non invia dati a nessun server proprio: profili, storico e saldi vivono solo nel
browser del dispositivo. Le uniche chiamate esterne sono verso i servizi pubblici di
OpenStreetMap e del MIMIT per geocodifica, percorsi e prezzi indicativi.

## Sviluppi futuri

Alcune idee (traffico live automatico, notifiche di promemoria, rilevamento movimento)
richiederebbero API a pagamento o un backend e sono annotate in [`BACKLOG.md`](BACKLOG.md).

## Licenza

Rilasciato con licenza [MIT](LICENSE).
