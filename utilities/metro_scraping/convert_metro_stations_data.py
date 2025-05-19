import json

input_file = 'all_moscow_stations.json'
output_file = 'data_metrostations.json'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

output_data = []
for item in data:
    output_data.append({
        "model": "realty_addresses.Metro",
        "pk": item["id"],
        "fields": {
            "line": item["line"], # Assuming 'line' in input is the MetroLine ID
            "name": item["name"],
            "name_full": item["name_full"],
            "geo_lat": item["geo_lat"],
            "geo_lon": item["geo_lon"],
            "is_closed": item["is_closed"]
        }
    })

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Successfully converted {input_file} to {output_file}")
