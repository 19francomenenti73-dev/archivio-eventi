import pandas as pd
import json
import os

EXCEL_FILE = "eventi.xlsx"      # Il file Excel che caricherai dal cellulare
GEOJSON_FILE = "events.geojson" # L'archivio ufficiale che alimenta la mappa

def merge_excel_to_geojson():
    if os.path.exists(GEOJSON_FILE):
        try:
            with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
        except Exception:
            geojson_data = {"type": "FeatureCollection", "features": []}
    else:
        geojson_data = {"type": "FeatureCollection", "features": []}

    if not os.path.exists(EXCEL_FILE):
        print(f"❌ File Excel '{EXCEL_FILE}' non trovato. Caricalo nel repository.")
        return

    try:
        df = pd.read_excel(EXCEL_FILE)
    except Exception as e:
        print(f"❌ Errore nella lettura del file Excel: {e}")
        return

    existing_features = geojson_data.get("features", [])
    
    existing_keys = {
        (
            f["geometry"]["coordinates"][1],
            f["geometry"]["coordinates"][0],
            f["properties"].get("titolo"),
            f["properties"].get("data_ora")
        )
        for f in existing_features
    }

    nuovi_inseriti = 0

    for _, row in df.iterrows():
        try:
            lat = float(row["lat"])
            lon = float(row["lon"])
            titolo = str(row.get("titolo", "Evento"))
            categoria = str(row.get("categoria", "Altro"))
            localita = str(row.get("localita", ""))
            data_ora = str(row.get("data_ora", ""))
            fonte_nome = str(row.get("fonte_nome", "Inserimento da Cellulare"))

            event_key = (lat, lon, titolo, data_ora)

            if event_key not in existing_keys:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "categoria": categoria,
                        "titolo": titolo,
                        "localita": localita,
                        "data_ora": data_ora,
                        "fonte_nome": fonte_nome
                    }
                }
                existing_features.append(feature)
                existing_keys.add(event_key)
                nuovi_inseriti += 1

        except Exception as err:
            print(f"⚠️ Errore in una riga dell'Excel (saltata): {err}")

    geojson_data["features"] = existing_features

    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Sincronizzazione completata! Aggiunti {nuovi_inseriti} nuovi eventi.")

if __name__ == "__main__":
    merge_excel_to_geojson()
    
