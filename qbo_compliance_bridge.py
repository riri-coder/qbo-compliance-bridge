import os
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

def process_receipt_logic(receipt_data, home_province="ON"):
    # --- 1. SETUP & DATA CLEANING ---
    # Handle list vs object format if Make sends an array
    if isinstance(receipt_data, list):
        receipt_data = receipt_data[0]

    vendor = receipt_data.get("vendor", "Unknown")
    province = receipt_data.get("province", home_province).upper()
    currency = receipt_data.get("currency", "CAD").upper()
    date_str = receipt_data.get("date", "")
    
    total_header = float(receipt_data.get("total", 0))
    # Extract individual taxes for the math reconciliation
    gst = float(receipt_data.get("gst", 0))
    pst = float(receipt_data.get("pst", 0))
    hst = float(receipt_data.get("hst", 0))
    tax_sum = gst + pst + hst

    global_flags = []
    
    # --- 2. CURRENCY CONVERSION ---
    usd_rate = 1.38
    conversion_factor = usd_rate if currency == "USD" else 1.0
    if currency == "USD":
        global_flags.append(f"Currency: Converted from USD at {usd_rate}")

    # --- 3. LINE ITEM PROCESSING ---
    processed_lines = []
    line_item_total_pre_tax = 0
    
    for item in receipt_data.get("line_items", []):
        desc = item.get("description", "No Description")
        raw_amount = float(item.get("amount", 0))
        line_item_total_pre_tax += raw_amount
        
        # Apply conversion to line amount for the output
        converted_amount = round(raw_amount * conversion_factor, 2)
        
        line_flags = []
        
        # RULE: $500 Threshold per line (CAD)
        if converted_amount >= 500:
            line_flags.append("FLAG: Capital Asset (> $500)")
            
        # RULE: Amazon Audit-Guard
        if "AMAZON" in vendor.upper() and len(desc) < 5:
            line_flags.append("FLAG: Vague Amazon Description")

        processed_lines.append({
            "description": desc,
            "amount_cad": converted_amount,
            "account_name": item.get("account_name"),
            "account_id": item.get("account_id"),
            "line_flags": line_flags
        })

    # --- 4. NEW: MATHEMATICAL AUDIT (The Gap Check) ---
    # Total - (Sum of Lines + Taxes)
    calculated_gap = round(total_header - (line_item_total_pre_tax + tax_sum), 2)

    if calculated_gap > 0.01:
        # Check for tip-heavy industries
        service_keywords = ["RESTAURANT", "BAR", "SALON", "TAXI", "UBER", "CAFE"]
        if any(word in vendor.upper() for word in service_keywords):
            global_flags.append(f"Auto-Reconcile: ${calculated_gap} Tip detected.")
        else:
            global_flags.append(f"RECONCILIATION: ${calculated_gap} unaccounted for.")
    elif calculated_gap < -0.01:
        global_flags.append(f"ERROR: Math mismatch. Items exceed total by ${abs(calculated_gap)}.")

    # --- 5. NEW: DATE AUDIT ---
    try:
        receipt_date = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now()
        if receipt_date > today:
            global_flags.append("DATE ERROR: Future date detected.")
        elif receipt_date < (today - timedelta(days=365)):
            global_flags.append("WARNING: Receipt is over 1 year old.")
    except:
        global_flags.append("FORMAT: Invalid or missing date.")

    # --- 6. COMPLIANCE (PST Split check) ---
    non_hst = ["BC", "SK", "MB", "QC"]
    if province != home_province and province in non_hst:
        global_flags.append(f"COMPLIANCE: {province} PST detected. Ensure PST is capitalized.")

    # --- 7. FINAL RESPONSE ASSEMBLY ---
    return {
        "vendor": vendor,
        "status": "Needs Review" if global_flags or any(l['line_flags'] for l in processed_lines) else "Clean",
        "audit_notes": " | ".join(global_flags) if global_flags else "Verified",
        "global_flags": global_flags, # Keeping this for your existing mappings
        "processed_lines": processed_lines,
        "total_cad": round(total_header * conversion_factor, 2)
    }

# --- THE WEB SERVER LAYER ---

@app.route('/', methods=['GET'])
def health_check():
    return "Bridge is Live!", 200

@app.route('/process', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        result = process_receipt_logic(data)
        return jsonify(result)
    except Exception as e:
        # This catches errors and sends them to Make instead of a generic 500
        return jsonify({"error": str(e), "status": "Error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
