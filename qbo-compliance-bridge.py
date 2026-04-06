import os
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

def process_receipt_logic(receipt_data, home_province="ON"):
    """
    Your Core Logic (The math and rules)
    """
    vendor = receipt_data.get("vendor", "Unknown")
    total_amount = float(receipt_data.get("total_amount", 0))
    currency = receipt_data.get("currency", "CAD").upper()
    tax_amount = float(receipt_data.get("tax_amount", 0))
    province = receipt_data.get("province", home_province).upper()
    description = receipt_data.get("description", "").strip()
    
    flags = []
    itc_claimable_gst = 0

    # --- RULE 4: CURRENCY CONVERSION ---
    usd_rate = 1.38 
    if currency == "USD":
        total_amount = round(total_amount * usd_rate, 2)
        tax_amount = round(tax_amount * usd_rate, 2)
        flags.append(f"Currency: Converted from USD at rate {usd_rate}")
        currency = "CAD"

    # --- RULE 1: CAPITAL ASSET REVIEW ---
    if total_amount >= 500.00:
        flags.append("FLAG: Capital Asset Review Required (> $500)")

    # --- RULE 2: THE PST SPLIT ---
    non_hst_provinces = ["BC", "SK", "MB", "QC"]
    if province != home_province and province in non_hst_provinces:
        itc_claimable_gst = round((total_amount / 1.12) * 0.05, 2)
        pst_portion = tax_amount - itc_claimable_gst
        flags.append(f"PST Split Applied: ${pst_portion} added to Cost Basis")
    else:
        itc_claimable_gst = tax_amount 

    # --- RULE 3: THE AMAZON FLAG ---
    if "AMAZON" in vendor.upper() and (not description or len(description) < 5):
        flags.append("FLAG: Missing Amazon Description (High Audit Risk)")

    return {
        "vendor": vendor,
        "final_cad_total": total_amount,
        "recoverable_itc_gst": itc_claimable_gst,
        "capitalized_cost": round(total_amount - itc_claimable_gst, 2),
        "flags": flags,
        "status": "Needs Review" if flags else "Clean"
    }

# --- THE WEB SERVER LAYER ---

@app.route('/', methods=['GET'])
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
