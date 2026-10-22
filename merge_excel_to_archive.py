import os
import json
import glob
import time
import re
import urllib.request
import urllib.parse
import pandas as pd

GEOJSON_FILE = "events.geojson"

def find_excel_file():
    files = glob.glob("*[Ee]venti*.xlsx") + glob.glob("*.xlsx") + glob.glob("*.xls")
    for f in files:
        if not os.path.basename(f).startswith("~$"):
            return f
    return None

def get_lat_lon_from_localita(localita_str):
    """Estrae la località principale (es. il Comune) isolandola da vie o strade e cerca le coordinate"""
    if not localita_str or localita_str == "Non specificata":
        return None, None
    
    tentativi = [localita_str]
    
    # Se la stringa contiene indicatori di via o strada, estrae la parte geografica principale prima di essi
    for sep in [' via ', ' viale ', ' piazza ', ' ss ', ' strada ', ' fiume ', ' località ', ' loc ']:
        if sep in localita_str.lower():
            parte_principale = localita_str.lower().split(sep)[0].strip()
            if parte_principale:
                tentativi.append(parte_principale)
    
    # Tentativo di pulizia generale da parole chiave superflue
    pulita = re.sub(r'\b(strada statale|statale|ss|via|viale|piazza|km|confine|prov|provincia|località|loc|del|della|alle|al|sul|sulla)\b\.?', '', localita_str, flags=re.IGNORECASE)
    tentativi.append(pulita.strip(' ,-/'))

    for q in tentativi:
        q_str = str(q).strip(' ,-/')
        if not q_str or len(q_str) < 2:
            continue
        try:
            query = f"{q_str}, Italia"
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
            
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'NowcastingItaliaBot/1.0'}
            )
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    print(f"🌍 Geocoding riuscito per '{localita_str}' (usato: '{q_str}'): ({lat}, {lon})")
                    return lat, lon
        except Exception as e:
            print(f"⚠️ Errore geocoding per '{q_str}': {e}")
        
        time.sleep(1)
        
    return None, None

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
    
    existing_keys = set()
    for feat in existing_features:
        try:
            coords = feat["geometry"]["coordinates"]
            d_ora = str(feat["properties"].get("data_ora", ""))
            existing_keys.add((coords[1], coords[0], d_ora))
        except KeyError:
            continue

    nuovi_inseriti = 0

    for row in df.to_dict(orient="records"):
        try:
            lat_val = row.get("lat") or row.get("latitude") or row.get("latitudine")
            lon_val = row.get("lon") or row.get("longitude") or row.get("longitudine") or row.get("lng")
            
            categoria = str(row.get("categoria") or row.get("evento") or "Evento Severo").strip()
            localita = str(row.get("localita") or row.get("località") or row.get("luogo") or "").strip()
            data_ora = str(row.get("data_ora") or row.get("data") or row.get("data/ora") or "Non specificata").strip()

            if not localita and (pd.isna(lat_val) or pd.isna(lon_val)):
                continue

            if pd.isna(lat_val) or pd.isna(lon_val) or str(lat_val).strip() == "" or str(lon_val).strip() == "":
                lat, lon = get_lat_lon_from_localita(localita)
                if lat is None or lon is None:
                    print(f"⚠️ Impossibile geocalizzare '{localita}': riga saltata.")
                    continue
                time.sleep(1)
            else:
                lat = float(str(lat_val).replace(",", "."))
                lon = float(str(lon_val).replace(",", "."))

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

        except Exception as e:
            print(f"⚠️ Errore in una riga Excel: {e}")

    geojson_data["features"] = existing_features

    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Sincronizzazione completata! Aggiunti {nuovi_inseriti} nuovi eventi. Totale: {len(existing_features)}")

if __name__ == "__main__":
    merge_excel_to_geojson()
            
