import json

input_file = 'all_moscow_lines.json'
output_file = 'data_metrolines.json'

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

output_data = []
for item in data:
    output_data.append({
        "model": "realty_addresses.MetroLine",
        "pk": item["id"],
        "fields": {
            "line_id": item["line_id"],
            "line_name": item["line_name"],
            "line_name_full": item["line_name_full"],
            "city": item["city"],
            "color": item["color"]
        }
    })

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Successfully converted {input_file} to {output_file}")
