# Backlog — sviluppi futuri

Funzionalità interessanti ma non implementate in questa sessione perché richiedono
API a pagamento, un backend, o hanno limiti tecnici sulle PWA che confliggono con
l'obiettivo di questa app (gratuita, offline-first, senza chiavi da configurare).

- **Traffico rilevato automaticamente** (senza inserimento manuale da Google Maps):
  richiederebbe una API a pagamento con traffico live (Google Routes, TomTom, HERE)
  e un piccolo proxy/backend per non esporre la chiave lato client.
- **Notifiche/promemoria** per registrare il traffico o per il pagamento a fine
  settimana: senza un backend con push notification, su una PWA sono realizzabili
  solo in modo limitato (solo mentre l'app è aperta), poco affidabili specialmente
  su iOS.
- **Suggerimento automatico del tragitto rilevando che l'utente è in movimento**:
  non esiste un'API di rilevamento attività affidabile e uniforme tra
  browser/PWA (specialmente su iOS Safari), è sperimentale e rischia di essere
  inaffidabile.
- **Widget di sistema**: le PWA non supportano widget nativi sulla home screen;
  l'unica cosa realistica è una scorciatoia rapida all'app.
