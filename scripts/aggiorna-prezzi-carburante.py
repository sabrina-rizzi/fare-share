#!/usr/bin/env python3
"""
Scarica i CSV pubblici dell'Osservatorio Prezzi Carburanti (MIMIT), calcola le
medie nazionali e per provincia di benzina, diesel e metano, e le salva in un
piccolo file JSON servito dalla stessa origine dell'app (GitHub Pages).

Questo evita il problema CORS del CSV originale e riduce il payload da alcuni MB
a poche decine di KB. Eseguito una volta al giorno da GitHub Actions.
"""
import json
import re
import sys
import datetime
import urllib.request

URL_PREZZI = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
URL_ANAGRAFICA = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
OUT = "prezzi-carburante.json"

# Intervallo plausibile per scartare errori di battitura nei dati grezzi
PREZZO_MIN, PREZZO_MAX = 0.4, 5.0

# Sotto questa soglia di rilevazioni, il dato di una provincia per un singolo
# carburante non è affidabile: l'app ricade sulla media nazionale per quel caso.
CAMPIONI_MINIMI_PROVINCIA = 5

# Nomi delle 107 province italiane attuali, indicizzati per sigla.
NOMI_PROVINCIA = {
    "TO": "Torino", "VC": "Vercelli", "NO": "Novara", "CN": "Cuneo", "AT": "Asti",
    "AL": "Alessandria", "BI": "Biella", "VB": "Verbano-Cusio-Ossola",
    "AO": "Aosta",
    "GE": "Genova", "IM": "Imperia", "SP": "La Spezia", "SV": "Savona",
    "MI": "Milano", "BG": "Bergamo", "BS": "Brescia", "CO": "Como", "CR": "Cremona",
    "LC": "Lecco", "LO": "Lodi", "MN": "Mantova", "MB": "Monza e della Brianza",
    "PV": "Pavia", "SO": "Sondrio", "VA": "Varese",
    "TN": "Trento", "BZ": "Bolzano",
    "VE": "Venezia", "VR": "Verona", "VI": "Vicenza", "TV": "Treviso",
    "PD": "Padova", "RO": "Rovigo", "BL": "Belluno",
    "TS": "Trieste", "GO": "Gorizia", "PN": "Pordenone", "UD": "Udine",
    "BO": "Bologna", "FE": "Ferrara", "FC": "Forlì-Cesena", "MO": "Modena",
    "PR": "Parma", "PC": "Piacenza", "RA": "Ravenna", "RE": "Reggio Emilia", "RN": "Rimini",
    "FI": "Firenze", "AR": "Arezzo", "GR": "Grosseto", "LI": "Livorno", "LU": "Lucca",
    "MS": "Massa-Carrara", "PI": "Pisa", "PT": "Pistoia", "PO": "Prato", "SI": "Siena",
    "PG": "Perugia", "TR": "Terni",
    "AN": "Ancona", "AP": "Ascoli Piceno", "FM": "Fermo", "MC": "Macerata", "PU": "Pesaro e Urbino",
    "RM": "Roma", "FR": "Frosinone", "LT": "Latina", "RI": "Rieti", "VT": "Viterbo",
    "AQ": "L'Aquila", "CH": "Chieti", "PE": "Pescara", "TE": "Teramo",
    "CB": "Campobasso", "IS": "Isernia",
    "NA": "Napoli", "AV": "Avellino", "BN": "Benevento", "CE": "Caserta", "SA": "Salerno",
    "BA": "Bari", "BT": "Barletta-Andria-Trani", "BR": "Brindisi", "FG": "Foggia",
    "LE": "Lecce", "TA": "Taranto",
    "PZ": "Potenza", "MT": "Matera",
    "CZ": "Catanzaro", "CS": "Cosenza", "KR": "Crotone", "RC": "Reggio Calabria", "VV": "Vibo Valentia",
    "PA": "Palermo", "AG": "Agrigento", "CL": "Caltanissetta", "CT": "Catania", "EN": "Enna",
    "ME": "Messina", "RG": "Ragusa", "SR": "Siracusa", "TP": "Trapani",
    "CA": "Cagliari", "NU": "Nuoro", "OR": "Oristano", "SS": "Sassari", "SU": "Sud Sardegna",
}


def scarica(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fare-share-price-updater"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def costruisci_mappa_province(testo_anagrafica):
    """idImpianto -> sigla provincia (2 lettere), scartando righe malformate."""
    mappa = {}
    righe = testo_anagrafica.split("\n")
    for r in righe[2:]:
        cols = r.split("|")
        if len(cols) < 8:
            continue
        id_impianto = cols[0].strip()
        provincia = cols[7].strip()
        if re.fullmatch(r"[A-Z]{2}", provincia) and provincia in NOMI_PROVINCIA:
            mappa[id_impianto] = provincia
    return mappa


def main():
    testo_prezzi = scarica(URL_PREZZI)
    try:
        testo_anagrafica = scarica(URL_ANAGRAFICA)
        mappa_province = costruisci_mappa_province(testo_anagrafica)
    except Exception as err:
        print("Anagrafica impianti non disponibile, salto le medie provinciali:", err, file=sys.stderr)
        mappa_province = {}

    righe = testo_prezzi.split("\n")

    data_estrazione = ""
    if righe:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", righe[0])
        if m:
            data_estrazione = m.group(1)

    acc_naz = {"benzina": [0.0, 0], "diesel": [0.0, 0], "metano": [0.0, 0]}
    acc_prov = {}  # sigla -> { benzina: [somma, conteggio], ... }

    for r in righe[2:]:
        cols = r.split("|")
        if len(cols) < 4:
            continue
        id_impianto = cols[0].strip()
        carburante = cols[1].strip()
        try:
            prezzo = float(cols[2])
        except ValueError:
            continue
        if not (PREZZO_MIN <= prezzo <= PREZZO_MAX):
            continue
        is_self = cols[3].strip() == "1"

        if carburante == "Metano":
            chiave = "metano"
        elif carburante == "Benzina" and is_self:
            chiave = "benzina"
        elif carburante == "Gasolio" and is_self:
            chiave = "diesel"
        else:
            continue

        acc_naz[chiave][0] += prezzo
        acc_naz[chiave][1] += 1

        provincia = mappa_province.get(id_impianto)
        if provincia:
            bucket = acc_prov.setdefault(provincia, {
                "benzina": [0.0, 0], "diesel": [0.0, 0], "metano": [0.0, 0]
            })
            bucket[chiave][0] += prezzo
            bucket[chiave][1] += 1

    def media(somma_conteggio):
        somma, conteggio = somma_conteggio
        return round(somma / conteggio, 3) if conteggio else None

    province_out = {}
    for sigla, bucket in acc_prov.items():
        voce = {"nome": NOMI_PROVINCIA.get(sigla, sigla), "campioni": {}}
        for chiave in ("benzina", "diesel", "metano"):
            somma, conteggio = bucket[chiave]
            voce["campioni"][chiave] = conteggio
            voce[chiave] = round(somma / conteggio, 3) if conteggio >= CAMPIONI_MINIMI_PROVINCIA else None
        province_out[sigla] = voce

    out = {
        "benzina": media(acc_naz["benzina"]),
        "diesel": media(acc_naz["diesel"]),
        "metano": media(acc_naz["metano"]),
        "dataEstrazione": data_estrazione,
        "aggiornatoIl": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "campioni": {k: acc_naz[k][1] for k in acc_naz},
        "fonte": "Osservatorio Prezzi Carburanti - MIMIT",
        "province": province_out,
    }

    if out["benzina"] is None and out["diesel"] is None and out["metano"] is None:
        print("Nessun prezzo valido trovato: non sovrascrivo il file.", file=sys.stderr)
        sys.exit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    print(
        "Scritto", OUT, "-> nazionale:",
        json.dumps({k: out[k] for k in ("benzina", "diesel", "metano", "dataEstrazione")}, ensure_ascii=False),
        "| province con dati:", len(province_out),
    )


if __name__ == "__main__":
    main()
