# QBO Canada Compliance Bridge (v1.0)

**A deterministic logic layer designed to bridge the gap between "Generative AI" extraction and "Audit-Ready" accounting data.**

---

## 📌 The Problem
Most AI-powered receipt tools (Dext, Hubdoc, OpenAI) operate on **probability**. They "guess" a category or tax rate based on patterns. For Canadian accounting, a "guess" is a liability. 

Common failure points in standard automation:
* **Asset Bloat:** AI categorizes a $1,200 laptop as "Office Supplies" because it's from Best Buy.
* **PST Leakage:** AI struggles to correctly split and capitalize non-recoverable PST for out-of-province purchases (BC, SK, MB, QC).
* **Vague Vendors:** Amazon receipts hit the ledger without descriptions, creating a nightmare for year-end audits.

## 🚀 The Solution
This Python-based "Logic Bridge" acts as a **Compliance Firewall**. It runs every AI-extracted receipt through a set of strict, firm-defined rules before the data is finalized.

### Key Logic Features:
* **The $500 Threshold:** Any transaction ≥ $500 is automatically flagged for "Capital Asset Review" to ensure correct depreciation scheduling.
* **Smart PST Splitting:** Detects the province of purchase. If it differs from the home province (e.g., Ontario), it automatically separates non-recoverable tax and adds it to the item's cost basis.
* **The Amazon Audit-Guard:** Proactively flags transactions from major vendors (Amazon, Walmart) that lack a specific item description.
* **Currency Engine:** Handles USD-to-CAD conversion using fixed or API-driven rates to ensure P&L accuracy for international SaaS/Travel.

## 🛠️ Technical Stack
* **Language:** Python 3.12+
* **Orchestration:** Make.com (Webhooks)
* **Intelligence:** OpenAI Vision API (Extraction)
* **Target:** QuickBooks Online (Canada)

## 📖 How to Use
1. **Extraction:** Send receipt image to the OpenAI module in Make.com.
2. **Logic Layer:** Route the JSON output to this Python script (hosted on PythonAnywhere or similar).
3. **Staging:** The script returns a "Status" (Clean vs. Review) and the corrected math.
4. **Finalization:** Clean entries are pushed to QBO; flagged entries are sent to a "Human-in-the-Loop" dashboard.

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Created by a Naturally Sync workflow consulting services.*
