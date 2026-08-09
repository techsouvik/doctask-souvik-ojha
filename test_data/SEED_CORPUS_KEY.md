# SEED CORPUS — ANSWER KEY (DO NOT DISTRIBUTE WITH SYSTEM)

## Project: Greenfield Tech Park — Phase 1
Fictional construction project in Bengaluru. All entities are invented.

## The Pile (8 documents)

| # | Filename | Format | Author/Source | Date | What it is |
|---|----------|--------|---------------|------|------------|
| 1 | master_project_plan.docx | DOCX | Apex Construction | 2024-01-08 | Original contract plan: scope, budget, timeline, milestones, penalty clauses |
| 2 | status_report_q1.pdf | PDF | Apex Construction (PM: Rakesh Menon) | 2024-04-05 | Q1 progress report covering Jan–Mar |
| 3 | status_report_q2.pdf | PDF | Apex Construction (PM: Rakesh Menon) | 2024-07-08 | Q2 progress report covering Apr–Jun |
| 4 | invoice_inv_2024_003.docx | DOCX | Apex Construction (Finance: Priya Nair) | 2024-08-12 | Invoice for Phase 3 superstructure |
| 5 | site_visit_minutes_jul.txt | TXT | Meridian Infra (Eng: Vikram Rao) | 2024-07-22 | Site visit meeting notes |
| 6 | contract_amendment_01.docx | DOCX | Joint (both parties) | 2024-07-30 | Time extension + budget revision |
| 7 | client_complaint_sep.txt | TXT | Meridian Infra (CEO: Anjali Deshmukh) | 2024-09-15 | Client complaint about delays |
| 8 | material_receipt_steel.pdf | PDF | Apex Construction (Store: Suresh Kumar) | 2024-04-20 | Delivery note for structural steel |

---

## THE GROUND TRUTH (what the system should extract)

### Key Facts across the pile
- **Project name:** Greenfield Tech Park, Phase 1
- **Location:** Plot 14-B, Electronic City Phase 2, Bengaluru 560100
- **Client:** Meridian Infrastructures Pvt Ltd
- **Contractor:** Apex Construction Ltd
- **Original contract value:** Rs 12.5 crores
- **Amended contract value:** Rs 14.2 crores (Amendment #1, 2024-07-30)
- **Original handover date:** 2024-12-15
- **Amended handover date:** 2025-03-31 (Amendment #1)
- **Original penalty clause:** 0.5% per week of delay, capped at 5% of contract value
- **Architect:** Stanton & Partners Architects
- **Structural consultant:** Dr. R. Kalyanaraman

### Phases and milestones (from master plan)
1. Site preparation & excavation — Jan to mid-Feb
2. Foundation — mid-Feb to Apr
3. Superstructure — May to Aug
4. MEP rough-in — Jul to Oct
5. Finishing — Oct to Dec
6. Handover & snagging — mid-Dec

---

## PLANTED ERRORS (what the system SHOULD catch)

### Error 1 — Arithmetic mismatch in Status Report Q1 (Document 2)
**Location:** Status Report Q1, page 2, "Financial Summary" section.
**The error:** The report states "Total expenditure to date: Rs 3.20 crores."
But the three phase expenditure line items listed below it sum to Rs 3.50 crores
(Site prep: 1.80 cr + Foundation: 1.10 cr + Initial structure: 0.60 cr = 3.50 cr).
The stated total (3.20 cr) is Rs 30 lakhs LESS than the actual sum (3.50 cr).
**Why it is subtle:** A reader skimming financial headlines sees a number that
looks reasonable for Q1 of a 12.5 crore project. You have to add the line items
to catch it. This is a common real-world error in manually typed status reports.

### Error 2 — Quantity contradiction within Status Report Q1 (Document 2)
**Location:** Status Report Q1. Narrative section says "8,500 cubic metres of
excavation completed." The Quantities Table on the same report lists excavation
as 7,200 cubic metres.
**Why it is subtle:** Same document, same metric, two numbers 1,300 units apart.
Both look plausible for a large site. Only caught if you cross-reference the
narrative against the table.

### Error 3 — Invoice bills a phase not yet completed (Document 4)
**Location:** Invoice INV-2024-003, dated 2024-08-12.
**The error:** The invoice bills Rs 2.80 crores for "Phase 3 — Superstructure
(100% complete)." But Status Report Q2 (dated 2024-07-08, only 5 weeks earlier)
reports Phase 3 as 40% complete. Per the master plan, Phase 3 was scheduled
May–Aug. Billing 100% for a phase that was 40% done five weeks prior is
contradictory. The master plan states milestone billing applies upon full
phase completion.
**Why it is subtle:** The invoice itself is perfectly formatted, correctly
addressed, has proper references, and the amount looks reasonable for a
superstructure phase. You only catch it by cross-referencing the invoice date
against the Q2 status report progress percentage. A reviewer rubber-stamping
invoices would miss it.

### Error 4 — Client complaint references wrong penalty rate (Document 7)
**Location:** Client complaint email, 2024-09-15.
**The error:** The client says "as per the 15% penalty clause in our agreement."
But the master project plan (Document 1, Section 12) specifies the penalty as
"0.5% per week of delay, capped at 5% of total contract value." There is no
15% penalty clause anywhere in the agreement.
**Why it is subtle:** The email reads as an angry client making a demand. The
wrong number sounds authoritative and is buried in an emotional paragraph.
Only caught by checking the actual contract text.

### Error 5 — Material receipt predates its own referenced PO delivery window (Document 8)
**Location:** Material Receipt Note for structural steel, dated 2024-04-20.
**The error:** The receipt references PO #APEX-PO-2024-029 and says "delivered
within agreed window." But Status Report Q1 (covering Jan–Mar, dated 2024-04-05)
states in its narrative that structural steel delivery was "expected by April 15"
— meaning the PO delivery window opened April 15. The receipt is dated April 20,
which is fine, but it also states "delivery lot 1 of 1, complete shipment."
Status Report Q2 then reports in July that steel delivery was delayed and only
70% had arrived by end of June. A "complete shipment" receipt on April 20
contradicts the Q2 report's claim of partial delivery through June.
**Why it is subtle:** Each document in isolation is self-consistent. The
contradiction only surfaces when you cross-reference the receipt against the
Q2 status report.

---

## WHAT A CLEAN DELIVERABLE LOOKS LIKE

The system's final output (the "register" or "brief") should:
1. List every document with its type, date, author, and key facts
2. Show the current reconciled project status (amended budget, amended timeline)
3. Flag every planted error above as a "finding" with exact source citation
4. Report "no findings" only if there genuinely are none (there are 5 here)
5. Update incrementally when a new document is added (not full re-run)
