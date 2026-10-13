import json
import os
from datetime import datetime

# File di output GeoJSON
GEOJSON_FILE = "events.geojson"

def load_geojson():
    """Carica il file GeoJSON esistente o ne crea una struttura vuota."""
    try:
        with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"type": "FeatureCollection", "features": []}

def save_geojson(data):
    """Salva i dati nel file GeoJSON formattato."""
    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_events():
    """
    Funzione di elaborazione conforme: gestisce eventi da fonti autorizzate 
    o inserimenti verificati senza scraping di testate giornalistiche.
    """
    geojson_data = load_geojson()
    
    # Esempio di struttura sicura per l'inserimento di eventi verificati
    # (Sostituire o popolare tramite feed open-data ufficiali autorizzati)
    eventi_verificati = [
        # {
        #     "titolo": "Evento di test verificato",
        #     "categoria": "Temporale Forte",
        #     "lat": 41.9028,
        #     "lon": 12.4964,
        #     "fonte_nome": "Open Data Protezione Civile / Fonte Ufficiale",
        #     "fonte_link": "https://example.com"
        # }
    ]

    nuovi_inserimenti = 0
    existing_links = {f["properties"].get("fonte_link") for f in geojson_data["features"]}

    for ev in eventi_verificati:
        if ev["fonte_link"] in existing_links:
            continue
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [ev["lon"], ev["lat"]]
            },
            "properties": {
                "categoria": ev["categoria"],
                "titolo": ev["titolo"],
                "data_ora": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "fonte_link": ev["fonte_link"],
                "fonte_nome": ev["fonte_nome"]
            }
        }
        
        geojson_data["features"].append(feature)
        nuovi_inserimenti += 1

    if nuovi_inserimenti > 0:
        save_geojson(geojson_data)
        print(f"Aggiunti {nuovi_inserimenti} nuovi eventi verificati all'archivio.")
    else:
        print("Nessun nuovo evento da aggiungere.")

if __name__ == "__main__":
    process_events()
    
