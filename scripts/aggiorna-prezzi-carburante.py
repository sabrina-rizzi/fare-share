#!/usr/bin/env python3
"""
Scarica il CSV pubblico dell'Osservatorio Prezzi Carburanti (MIMIT), calcola le
medie nazionali indicative di benzina, diesel e metano e le salva in un piccolo
file JSON servito dalla stessa origine dell'app (GitHub Pages).

Questo evita il problema CORS del CSV originale e riduce il payload da ~4 MB a
poche centinaia di byte. Eseguito una volta al giorno da GitHub Actions.
"""
import json
import re
import sys
import datetime
import urllib.request

URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
OUT = "prezzi-carburante.json"

# Intervallo plausibile per scartare errori di battitura nei dati grezzi
PREZZO_MIN, PREZZO_MAX = 0.4, 5.0


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "fare-share-price-updater"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    righe = raw.split("\n")

    data_estrazione = ""
    if righe:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", righe[0])
        if m:
            data_estrazione = m.group(1)

    acc = {"benzina": [0.0, 0], "diesel": [0.0, 0], "metano": [0.0, 0]}

    # riga 0 = intestazione "Estrazione del ...", riga 1 = header colonne, dati dalla 2
    for r in righe[2:]:
        cols = r.split("|")
        if len(cols) < 4:
            continue
        carburante = cols[1].strip()
        try:
            prezzo = float(cols[2])
        except ValueError:
            continue
        if not (PREZZO_MIN <= prezzo <= PREZZO_MAX):
            continue
        is_self = cols[3].strip() == "1"

        # Il metano è quasi sempre servito (non self): lo conteggiamo a prescindere.
        if carburante == "Metano":
            acc["metano"][0] += prezzo
            acc["metano"][1] += 1
            continue
        if not is_self:
            continue
        if carburante == "Benzina":
            acc["benzina"][0] += prezzo
            acc["benzina"][1] += 1
        elif carburante == "Gasolio":
            acc["diesel"][0] += prezzo
            acc["diesel"][1] += 1

    def media(chiave):
        somma, conteggio = acc[chiave]
        return round(somma / conteggio, 3) if conteggio else None

    out = {
        "benzina": media("benzina"),
        "diesel": media("diesel"),
        "metano": media("metano"),
        "dataEstrazione": data_estrazione,
        "aggiornatoIl": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "campioni": {k: acc[k][1] for k in acc},
        "fonte": "Osservatorio Prezzi Carburanti - MIMIT",
    }

    if out["benzina"] is None and out["diesel"] is None and out["metano"] is None:
        print("Nessun prezzo valido trovato: non sovrascrivo il file.", file=sys.stderr)
        sys.exit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("Scritto", OUT, "->", json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
