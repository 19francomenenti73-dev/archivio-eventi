import pandas as pd
import json
import os
import glob

GEOJSON_FILE = "events.geojson"

def find_excel_file():
    files = glob.glob("*[Xx][Ll][Ss][Xx]*")
    if not files:
        files = glob.glob("*.xlsx") + glob.glob("*.XLSX")
    if not files:
        return None
    for f in files:
        if not f.startswith("~$") and f != GEOJSON_FILE:
            return f
    return None

def merge_excel_to_geojson():
    if os.path.exists(GEOJSON_FILE):
        try:
            with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
                geojson_data = json.load(f)
        except Exception:
            geojson_data = {"type": "FeatureCollection", "features": []}
    else:
        geojson_data = {"type": "FeatureCollection", "features": []}

    excel_file = find_excel_file()
    if not excel_file:
        print("❌ Nessun file Excel trovato nel repository.")
        return

    print(f"📂 Trovato file: {excel_file}")

    try:
        df = pd.read_excel(excel_file)
        df.columns = [str(c).strip().lower() for c in df.columns]
    except Exception as e:
        print(f"❌ Errore nella lettura del file Excel: {e}")
        return

    existing_features = geojson_data.get("features", [])
    
    existing_keys = {
        (
            f["geometry"]["coordinates"][1],
            f["geometry"]["coordinates"][0],
            str(f["properties"].get("data_ora"))
        )
        for f in existing_features
    }

    nuovi_inseriti = 0

    for _, row in df.iterrows():
        try:
            lat_val = row.get("lat") or row.get("latitudine")
            lon_val = row.get("lon") or row.get("longitudine")
            
            if pd.isna(lat_val) or pd.isna(lon_val):
                continue
                
            lat = float(str(lat_val).replace(',', '.'))
            lon = float(str(lon_val).replace(',', '.'))
            
            categoria = str(row.get("categoria", "Evento"))
            localita = str(row.get("localita", row.get("località", "")))
            data_ora = str(row.get("data_ora", row.get("data", "")))

            event_key = (lat, lon, data_ora)

            if event_key not in existing_keys:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "categoria": categoria,
                        "localita": localita,
                        "data_ora": data_ora
                    }
                }
                existing_features.append(feature)
                existing_keys.add(event_key)
                nuovi_inseriti += 1

        except Exception as err:
            print(f"⚠️ Errore in una riga (saltata): {err}")

    geojson_data["features"] = existing_features

    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Sincronizzazione completata! Aggiunti {nuovi_inseriti} nuovi eventi. Totale eventi in archivio: {len(existing_features)}")

if __name__ == "__main__":
    merge_excel_to_geojson()
  
