import json

def process_receipt_logic(receipt_data, home_province="ON"):
    """
    Processes raw receipt data through Canadian accounting compliance rules.
    """
    
    # 1. Initialize variables from raw AI data
    vendor = receipt_data.get("vendor", "Unknown")
    total_amount = float(receipt_data.get("total_amount", 0))
    currency = receipt_data.get("currency", "CAD").upper()
    tax_amount = float(receipt_data.get("tax_amount", 0))
    province = receipt_data.get("province", home_province).upper()
    description = receipt_data.get("description", "").strip()
    
    # Logic Flags & Final Values
    flags = []
    final_accounting_total = total_amount
    itc_claimable_gst = 0
    cost_basis_increase = 0

    # --- RULE 4: CURRENCY CONVERSION (USD TO CAD) ---
    # In 2026, many contractors pay for software in USD.
    usd_rate = 1.38  # Example mid-market rate for April 2026
    if currency == "USD":
        total_amount = round(total_amount * usd_rate, 2)
        tax_amount = round(tax_amount * usd_rate, 2)
        flags.append(f"Currency: Converted from USD at rate {usd_rate}")
        currency = "CAD"

    # --- RULE 1: CAPITAL ASSET REVIEW ($500 RULE) ---
    # Prevents high-value items from being hidden in 'Office Supplies'
    if total_amount >= 500.00:
        flags.append("FLAG: Capital Asset Review Required (> $500)")

    # --- RULE 2: THE PST SPLIT (NON-HOME PROVINCE) ---
    # Logic: Only GST (5%) is generally recoverable as an ITC in non-HST provinces.
    # The PST portion should be added to the cost of the item, not the tax account.
    non_hst_provinces = ["BC", "SK", "MB", "QC"]
    
    if province != home_province and province in non_hst_provinces:
        # Simplified math: Assuming 5% GST is the only recoverable part
        itc_claimable_gst = round((total_amount / 1.12) * 0.05, 2) # Example for 12% total tax
        pst_portion = tax_amount - itc_claimable_gst
        cost_basis_increase = pst_portion
        flags.append(f"PST Split Applied: ${pst_portion} added to Cost Basis (Non-recoverable {province} tax)")
    else:
        itc_claimable_gst = tax_amount # Assume full HST is recoverable if in home province

    # --- RULE 3: THE AMAZON "VAGUE DESCRIPTION" FLAG ---
    # Accountants spend hours chasing clients for what was actually in the box.
    if "AMAZON" in vendor.upper() and (not description or len(description) < 5):
        flags.append("FLAG: Missing Amazon Description (High Audit Risk)")

    # --- OUTPUT PREPARATION ---
    output = {
        "vendor": vendor,
        "final_cad_total": total_amount,
        "recoverable_itc_gst": itc_claimable_gst,
        "capitalized_cost": round(total_amount - itc_claimable_gst, 2),
        "flags": flags,
        "status": "Needs Review" if flags else "Clean"
    }
    
    return output

# --- TEST CASE: AN OUT-OF-PROVINCE AMAZON PURCHASE ---
raw_input = {
    "vendor": "Amazon.ca",
    "total_amount": 650.00,
    "currency": "USD",
    "tax_amount": 78.00,
    "province": "BC",
    "description": "" # Empty description test
}

processed_result = process_receipt_logic(raw_input)

print(json.dumps(processed_result, indent=4))