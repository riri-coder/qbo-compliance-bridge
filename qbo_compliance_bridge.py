import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def process_receipt_logic(receipt_data, home_province="ON"):
    vendor = receipt_data.get("vendor", "Unknown")
    province = receipt_data.get("province", home_province).upper()
    currency = receipt_data.get("currency", "CAD").upper()
    total_header = float(receipt_data.get("total", 0))
    
    # Global Flags
    flags = []
    
    # 1. Handle Currency Conversion for the whole batch
    usd_rate = 1.38
    conversion_factor = usd_rate if currency == "USD" else 1.0
    if currency == "USD":
        flags.append(f"Currency: Converted from USD at {usd_rate}")

    processed_lines = []
    
    # 2. Process each line item individually
    for item in receipt_data.get("line_items", []):
        desc = item.get("description", "No Description")
        # Apply conversion factor to the line amount
        raw_amount = float(item.get("amount", 0)) * conversion_factor
        
        line_flags = []
        
        # RULE: $500 Threshold per line
        if raw_amount >= 500:
            line_flags.append("FLAG: Capital Asset (> $500)")
            
        # RULE: Amazon Audit-Guard
        if "AMAZON" in vendor.upper() and len(desc) < 5:
            line_flags.append("FLAG: Vague Amazon Description")

        processed_lines.append({
            "description": desc,
            "amount_cad": round(raw_amount, 2),
            "account_name": item.get("account_name"),
            "account_id": item.get("account_id"),
            "line_flags": line_flags
        })

    # 3. Summary Compliance Logic (PST Split check)
    non_hst = ["BC", "SK", "MB", "QC"]
    if province != home_province and province in non_hst:
        flags.append(f"COMPLIANCE: {province} PST detected. Ensure PST portion is capitalized in QBO.")

    return {
        "vendor": vendor,
        "status": "Needs Review" if flags or any(l['line_flags'] for l in processed_lines) else "Clean",
        "global_flags": flags,
        "processed_lines": processed_lines,
        "total_cad": round(total_header * conversion_factor, 2)
    }

# --- THE WEB SERVER LAYER ---

@app.route('/', methods=['POST'])
def health_check():
    return "Bridge is Live!", 200

@app.route('/process', methods=['POST'])
def webhook():
    # Grab the JSON data sent from Make.com
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Run the logic
    result = process_receipt_logic(data)
    
    # Send the result back to Make.com
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
