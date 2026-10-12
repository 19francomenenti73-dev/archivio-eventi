import feedparser
import json
import re
import urllib.parse
import urllib.request
import time
from datetime import datetime

# Feed RSS di testate giornalistiche e fonti di cronaca/meteo
RSS_FEEDS = [
    "https://www.ansa.it/sitemap/tecnologia/rss.xml", # Sostituisci o aggiungi i feed RSS desiderati
    "https://www.meteoitalianotizie.it/feed/",
]

# Parole chiave per la classificazione dei fenomeni severi
KEYWORDS = {
    "Tornado / Tromba d'aria": [r"\btornado\b", r"\btromba d'aria\b"],
    "Tromba Marina": [r"\btromba marina\b"],
    "Grandine": [r"\bgrandinat[ae]\b", r"\bgrandine\b"],
    "Flash Flood / Allagamento": [r"\ballagament[oi]\b", r"\bflash flood\b", r"\bbomba d'acqua\b"],
    "Frana / Smottamento": [r"\bfran[ae]\b", r"\bsmottament[oi]\b"]
}

GEOJSON_FILE = "events.geojson"

def load_geojson():
    try:
        with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"type": "FeatureCollection", "features": []}

def save_geojson(data):
    with open(GEOJSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def geocode(location_name):
    """Geocoding tramite OpenStreetMap Nominatim API (100% gratuito e pubblico)"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(location_name + ', Italia')}&format=json&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'NowcastingItaliaTracker/1.0'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode())
            if res:
                return float(res[0]['lat']), float(res[0]['lon'])
    except Exception as e:
        print(f"Errore geocoding per {location_name}: {e}")
    return None, None

def process_rss():
    geojson_data = load_geojson()
    existing_urls = {f["properties"]["fonte_link"] for f in geojson_data["features"] if "fonte_link" in f["properties"]}
    
    new_events = 0
    
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            link = entry.get("link", "")
            if link in existing_urls:
                continue
            
            text_to_check = f"{entry.get('title', '')} {entry.get('summary', '')}"
            
            detected_category = None
            for cat, regexes in KEYWORDS.items():
                if any(re.search(r, text_to_check, re.IGNORECASE) for r in regexes):
                    detected_category = cat
                    break
            
            if detected_category:
                title = entry.get('title', '')
                lat, lon = geocode(title) 
                if lat and lon:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "categoria": detected_category,
                            "titolo": title,
                            "data_ora": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "fonte_link": link,
                            "fonte_nome": feed.feed.get('title', 'Fonte Giornalistica')
                        }
                    }
                    geojson_data["features"].append(feature)
                    existing_urls.add(link)
                    new_events += 1
                    time.sleep(1) # Rispetto dei rate limit delle API pubbliche
                    
    if new_events > 0:
        save_geojson(geojson_data)
        print(f"Aggiunti {new_events} nuovi eventi severi all'archivio!")

if __name__ == "__main__":
    process_rss()
  
