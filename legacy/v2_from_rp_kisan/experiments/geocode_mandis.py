"""Geocode the 20 selected mandis with OpenStreetMap Nominatim (1 request/second)."""
import json, time, urllib.parse, urllib.request, csv

MANDIS = {  # AGMARKNET market name -> place query used for geocoding
    "Bhikhi APMC": "Bhikhi, Mansa, Punjab, India",
    "Boha APMC": "Boha, Mansa, Punjab, India",
    "Amargarh APMC": "Amargarh, Malerkotla, Punjab, India",
    "Abohar APMC": "Abohar, Fazilka, Punjab, India",
    "Sangat APMC": "Sangat Mandi, Bathinda, Punjab, India",
    "Sahnewal APMC": "Sahnewal, Ludhiana, Punjab, India",
    "Jalalabad APMC": "Jalalabad, Fazilka, Punjab, India",
    "Jalandhar City APMC": "Jalandhar, Punjab, India",
    "Rayya APMC": "Rayya, Amritsar, Punjab, India",
    "Bhawanigarh APMC": "Bhawanigarh, Sangrur, Punjab, India",
    "Jaitu APMC": "Jaitu, Faridkot, Punjab, India",
    "Sadiq APMC": "Sadiq, Faridkot, Punjab, India",
    "Talwandi Bhai APMC": "Talwandi Bhai, Firozpur, Punjab, India",
    "Chanarthal APMC": "Chanarthal Kalan, Fatehgarh Sahib, Punjab, India",
    "Jalandhar City(Kartar Pur Dana mandi) APMC": "Kartarpur, Jalandhar, Punjab, India",
    "Kahnuwan APMC": "Kahnuwan, Gurdaspur, Punjab, India",
    "Patran APMC": "Patran, Patiala, Punjab, India",
    "Jalandhar Cantt. APMC": "Jalandhar Cantonment, Jalandhar, Punjab, India",
    "Patiala(New Anaj Mandi) APMC": "Patiala, Punjab, India",
    "Dhilwan APMC": "Dhilwan, Kapurthala, Punjab, India",
}

rows = []
for market, q in MANDIS.items():
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": q, "format": "json", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "KisanNiti-research-geocoder/0.1 (student project)"})
    res = json.load(urllib.request.urlopen(req, timeout=30))
    r = res[0] if res else {}
    rows.append({"market_name": market, "query": q, "lat": r.get("lat", ""), "lon": r.get("lon", ""), "osm_display_name": r.get("display_name", "")})
    print(market, "|", r.get("lat"), r.get("lon"), "|", r.get("display_name", "NOT FOUND")[:110])
    time.sleep(1.1)

with open("mandi_coordinates.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
