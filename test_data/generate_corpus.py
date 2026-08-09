#!/usr/bin/env python3
"""Generate the Greenfield Tech Park seed corpus — 8 documents with 5 planted errors."""
import os
from docx import Document
from docx.shared import Pt, Inches
from fpdf import FPDF

BASE = os.path.join(os.path.dirname(__file__), "greenfield_tech_park")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 1: MASTER PROJECT PLAN (DOCX)
# ═══════════════════════════════════════════════════════════════
def gen_master_plan():
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    doc.add_heading('MASTER PROJECT PLAN', level=0)
    doc.add_heading('Greenfield Tech Park — Phase 1', level=1)

    meta = [
        ('Document Ref', 'APEX-MPP-2024-001'),
        ('Date', '8 January 2024'),
        ('Prepared by', 'Apex Construction Ltd'),
        ('Prepared for', 'Meridian Infrastructures Pvt Ltd'),
    ]
    for label, val in meta:
        p = doc.add_paragraph()
        p.add_run(f'{label}: ').bold = True
        p.add_run(val)

    doc.add_heading('1. Project Overview', level=1)
    doc.add_paragraph(
        'This Master Project Plan governs the design and construction of Greenfield '
        'Tech Park Phase 1, a Grade-A commercial office development located at Plot 14-B, '
        'Electronic City Phase 2, Bengaluru 560100. The project comprises two basement '
        'levels for parking, a ground-floor retail podium, and fourteen upper floors of '
        'leasable office space, totalling approximately 4,80,000 square feet of built-up area.'
    )

    doc.add_heading('2. Parties', level=1)
    for item in [
        'Client (hereinafter "the Employer"): Meridian Infrastructures Pvt Ltd, represented by its authorised signatory.',
        'Contractor (hereinafter "the Contractor"): Apex Construction Ltd, represented by its Managing Director.',
        'Architect: Stanton & Partners Architects.',
        'Structural Consultant: Dr. R. Kalyanaraman, F.I.Struct.E.',
    ]:
        doc.add_paragraph(item, style='List Bullet')

    doc.add_heading('3. Scope of Work', level=1)
    doc.add_paragraph(
        'The Contractor shall execute all civil, structural, mechanical, electrical, and '
        'plumbing works necessary to complete and hand over the project on a turnkey basis, '
        'in accordance with the drawings, specifications, and BoQ appended to this agreement.'
    )

    doc.add_heading('4. Contract Value', level=1)
    doc.add_paragraph(
        'The total contract value is fixed at Rupees Twelve Crores and Fifty Lakhs only '
        '(Rs 12,50,00,000), inclusive of all taxes, levies, and statutory dues. This amount '
        'shall be adjusted only through a duly executed variation order or contract amendment.'
    )
    p = doc.add_paragraph()
    p.add_run('Payment milestones: ').bold = True
    p.add_run(
        'Payments shall be released against achieved milestones as defined in Schedule B. '
        'Each milestone payment becomes due upon certified completion of the corresponding phase '
        'by the Architect.'
    )

    doc.add_heading('5. Project Timeline', level=1)
    doc.add_paragraph('The project shall be executed in six phases:')
    phases = [
        ('Phase 1', 'Site preparation and excavation', '1 January 2024 to 15 February 2024'),
        ('Phase 2', 'Foundation and sub-structure', '15 February 2024 to 30 April 2024'),
        ('Phase 3', 'Superstructure (RCC frames, slabs, walls)', '1 May 2024 to 31 August 2024'),
        ('Phase 4', 'MEP rough-in (electrical, HVAC, plumbing)', '1 July 2024 to 31 October 2024'),
        ('Phase 5', 'Finishing and facade', '1 October 2024 to 15 December 2024'),
        ('Phase 6', 'Handover, testing, and snagging', '15 December 2024 to 31 December 2024'),
    ]
    for phase, desc, timeline in phases:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(f'{phase} - {desc}: ').bold = True
        p.add_run(timeline)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run('Project handover date: ').bold = True
    p.add_run('15 December 2024.')

    doc.add_heading('6. Milestone Payments (Schedule B)', level=1)
    milestones = [
        ('M1', 'Site preparation and excavation complete', '10% of contract value', '15 February 2024'),
        ('M2', 'Foundation complete', '20% of contract value', '30 April 2024'),
        ('M3', 'Superstructure complete', '25% of contract value', '31 August 2024'),
        ('M4', 'MEP rough-in complete', '20% of contract value', '31 October 2024'),
        ('M5', 'Finishing complete', '15% of contract value', '15 December 2024'),
        ('M6', 'Handover and snagging complete', '10% of contract value (less retention)', '31 December 2024'),
    ]
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Milestone'
    hdr[1].text = 'Description'
    hdr[2].text = 'Payment'
    hdr[3].text = 'Due Date'
    for m, d, pay, dt in milestones:
        row = table.add_row().cells
        row[0].text = m
        row[1].text = d
        row[2].text = pay
        row[3].text = dt

    doc.add_heading('7. Quality and Materials', level=1)
    doc.add_paragraph(
        'All materials shall conform to IS specifications or their equivalent international '
        'standards as approved by the Architect. Structural concrete shall be M40 grade for '
        'columns and M35 for slabs. Reinforcement steel shall be Fe500D conforming to IS 1786. '
        'The Contractor shall submit material test certificates for all major procurements prior '
        'to incorporation in the works.'
    )

    doc.add_heading('8. Insurance and Safety', level=1)
    doc.add_paragraph(
        'The Contractor shall maintain Contractors All Risks insurance and Workmens '
        'Compensation insurance for the full duration of the project, with cover amounts '
        'not less than 110% of the contract value. A comprehensive site safety plan conforming '
        'to the Building and Other Construction Workers Act, 1996 shall be maintained at all times.'
    )

    doc.add_heading('9. Force Majeure', level=1)
    doc.add_paragraph(
        'Neither party shall be liable for any delay or failure in performance resulting '
        'from events beyond its reasonable control, including but not limited to acts of God, '
        'war, civil unrest, pandemic, government regulation, or extreme weather conditions '
        'lasting more than seventy-two hours. The affected party shall notify the other in '
        'writing within seven days of the event.'
    )

    doc.add_heading('10. Dispute Resolution', level=1)
    doc.add_paragraph(
        'Any dispute arising out of this agreement shall first be referred to mutual discussion '
        'between senior management of both parties. Failing resolution within thirty days, the '
        'dispute shall be referred to arbitration under the Arbitration and Conciliation Act, 1996, '
        'with a sole arbitrator appointed by mutual consent. The venue of arbitration shall be Bengaluru.'
    )

    doc.add_heading('11. Defect Liability Period', level=1)
    doc.add_paragraph(
        'The Contractor shall remain liable for defects in workmanship or materials for a period '
        'of twenty-four (24) months from the date of certified handover. A retention amount equal '
        'to 5% of the contract value shall be held back and released in two equal instalments at '
        'the end of the first and second years of the defect liability period, subject to rectification '
        'of any notified defects.'
    )

    doc.add_heading('12. Liquidated Damages (Penalty Clause)', level=1)
    doc.add_paragraph(
        'In the event that the Contractor fails to achieve the project handover date specified '
        'in Section 5, liquidated damages shall be levied at the rate of 0.5% (zero point five '
        'percent) of the total contract value per week of delay, subject to a maximum cap of '
        '5% (five percent) of the total contract value. Time is of the essence in this agreement. '
        'Liquidated damages shall be deducted from amounts otherwise due to the Contractor or '
        'recovered from the retention. The Employer reserves the right to terminate the contract '
        'if the delay exceeds 180 days beyond the agreed handover date.'
    )

    doc.add_heading('13. Variation Orders', level=1)
    doc.add_paragraph(
        'Any variation to the scope, specifications, or value of the contract shall be executed '
        'through a formal Variation Order signed by authorised representatives of both parties. '
        'No verbal instructions shall constitute a variation.'
    )

    doc.add_heading('14. Governing Law', level=1)
    doc.add_paragraph(
        'This agreement shall be governed by and construed in accordance with the laws of India. '
        'The courts at Bengaluru shall have exclusive jurisdiction.'
    )

    doc.add_paragraph()
    doc.add_paragraph('--- END OF DOCUMENT ---')
    p = doc.add_paragraph()
    p.add_run('Signed for and on behalf of Apex Construction Ltd:\n').bold = True
    doc.add_paragraph('______________________________')
    p = doc.add_paragraph()
    p.add_run('Signed for and on behalf of Meridian Infrastructures Pvt Ltd:\n').bold = True
    doc.add_paragraph('______________________________')

    path = os.path.join(BASE, 'contracts', 'master_project_plan.docx')
    doc.save(path)
    print(f"  [1/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 2: STATUS REPORT Q1 (PDF) — HAS ERRORS 1 & 2
# ═══════════════════════════════════════════════════════════════
def gen_status_q1():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'QUARTERLY STATUS REPORT - Q1 (January - March 2024)', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font('Helvetica', '', 10)
    for line in [
        'Project: Greenfield Tech Park - Phase 1',
        'Report Ref: APEX-QR-2024-Q1',
        'Period: 1 January 2024 to 31 March 2024',
        'Date of Report: 5 April 2024',
        'Prepared by: Rakesh Menon, Project Manager, Apex Construction Ltd',
        'Submitted to: Meridian Infrastructures Pvt Ltd',
    ]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Executive Summary
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '1. Executive Summary', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5,
        'The first quarter saw the successful completion of site preparation, excavation, '
        'and the commencement of foundation works. Approximately 8,500 cubic metres of '
        'excavation were completed across the site footprint. The foundation raft pour '
        'began on schedule in the third week of March. No lost-time incidents were recorded '
        'during the quarter. The project remains on track against the baseline schedule.'
    )
    pdf.ln(3)

    # Progress by Phase
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '2. Progress by Phase', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    for line in [
        'Phase 1 (Site Preparation and Excavation): 100% complete. Achieved on 18 February 2024, three days behind the planned date of 15 February.',
        'Phase 2 (Foundation and Sub-structure): 65% complete as of 31 March 2024. Raft concrete pour commenced 22 March. Basement retaining walls in progress.',
        'Phase 3 onwards: Not yet commenced.',
    ]:
        pdf.multi_cell(0, 5, line)
        pdf.ln(1)

    # Quantities Table
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '3. Quantities Executed This Quarter', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 7, 'Item', border=1)
    pdf.cell(50, 7, 'Unit', border=1)
    pdf.cell(50, 7, 'Quantity', border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    # ERROR 2: Table says 7,200 cum but narrative above says 8,500 cum
    qt_items = [
        ('Excavation', 'Cubic Metres', '7,200'),
        ('PCC (Plain Cement Concrete)', 'Cubic Metres', '480'),
        ('Reinforcement Steel (foundation)', 'Tonnes', '185'),
        ('Raft Concrete M35', 'Cubic Metres', '1,250'),
    ]
    for item, unit, qty in qt_items:
        pdf.cell(60, 7, item, border=1)
        pdf.cell(50, 7, unit, border=1)
        pdf.cell(50, 7, qty, border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Financial Summary
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '4. Financial Summary', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    # ERROR 1: Total says 3.20 cr but items sum to 3.50 cr
    pdf.multi_cell(0, 5, 'Total expenditure to date: Rs 3.20 crores')
    pdf.ln(1)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(80, 7, 'Phase', border=1)
    pdf.cell(80, 7, 'Expenditure (Rs Crores)', border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    fin_items = [
        ('Site preparation and excavation', '1.80'),
        ('Foundation works', '1.10'),
        ('Initial superstructure (adv.)', '0.60'),
    ]
    for phase, amt in fin_items:
        pdf.cell(80, 7, phase, border=1)
        pdf.cell(80, 7, amt, border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Look-ahead
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '5. Look-Ahead (Q2)', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5,
        'Foundation works are expected to achieve 100% completion by 30 April 2024. '
        'Procurement of structural steel for the superstructure is in progress; the first '
        'steel delivery is expected by 15 April 2024. Superstructure RCC work will commence '
        'in the first week of May.'
    )
    pdf.ln(3)
    pdf.multi_cell(0, 5,
        'No variations or claims were raised during the quarter. No safety incidents or '
        'environmental non-conformances were reported.'
    )
    pdf.ln(5)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.cell(0, 5, '--- END OF REPORT ---', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, 'Prepared by: Rakesh Menon, Project Manager', new_x="LMARGIN", new_y="NEXT")

    path = os.path.join(BASE, 'reports', 'status_report_q1.pdf')
    pdf.output(path)
    print(f"  [2/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 3: STATUS REPORT Q2 (PDF) — needed for errors 3 & 5
# ═══════════════════════════════════════════════════════════════
def gen_status_q2():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'QUARTERLY STATUS REPORT - Q2 (April - June 2024)', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font('Helvetica', '', 10)
    for line in [
        'Project: Greenfield Tech Park - Phase 1',
        'Report Ref: APEX-QR-2024-Q2',
        'Period: 1 April 2024 to 30 June 2024',
        'Date of Report: 8 July 2024',
        'Prepared by: Rakesh Menon, Project Manager, Apex Construction Ltd',
        'Submitted to: Meridian Infrastructures Pvt Ltd',
    ]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '1. Executive Summary', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5,
        'The second quarter focused on completing the foundation and advancing the '
        'superstructure. Phase 2 (Foundation) was completed on 2 May 2024, two days '
        'behind schedule. Phase 3 (Superstructure) commenced on 6 May and is currently '
        '40% complete. RCC column casting up to the 5th floor has been achieved. '
        'Structural steel delivery experienced delays; only approximately 70% of the '
        'ordered steel had been received by end of June, impacting the beam erection '
        'schedule for the upper floors.'
    )
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '2. Progress by Phase', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    for line in [
        'Phase 2 (Foundation): 100% complete. Certified by Architect on 2 May 2024.',
        'Phase 3 (Superstructure): 40% complete as of 30 June 2024. Columns cast up to 5th floor. Slab pours completed up to 3rd floor.',
        'Phase 4 (MEP rough-in): Preliminary work commenced on 20 June 2024.',
    ]:
        pdf.multi_cell(0, 5, line)
        pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '3. Material Procurement', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5,
        'Structural steel (Fe500D, IS 1786) procurement against PO #APEX-PO-2024-029 '
        'experienced delays attributable to supplier production backlog. As of 30 June 2024, '
        'approximately 70% of the total ordered tonnage has been received at site. The '
        'remaining quantity is expected by mid-July. This delay has impacted the beam '
        'erection schedule for floors 6 and above. Cement and aggregate supplies remain '
        'on schedule with no disruption.'
    )
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '4. Financial Summary', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, 'Total expenditure to date: Rs 6.80 crores')
    pdf.ln(1)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(80, 7, 'Phase', border=1)
    pdf.cell(80, 7, 'Cumulative (Rs Crores)', border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    q2_fin = [
        ('Site preparation and excavation', '1.80'),
        ('Foundation works (complete)', '2.50'),
        ('Superstructure (in progress)', '2.50'),
    ]
    for phase, amt in q2_fin:
        pdf.cell(80, 7, phase, border=1)
        pdf.cell(80, 7, amt, border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, '5. Issues and Risks', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    for line in [
        'Steel delivery delay (as above) may impact the Phase 3 completion date of 31 August 2024. Mitigation: expedited delivery and weekend shift work.',
        'One minor safety incident (finger injury, no lost time) on 12 June. Corrective action implemented.',
        'No claims or variations raised during the quarter.',
    ]:
        pdf.multi_cell(0, 5, line)
        pdf.ln(1)

    pdf.ln(5)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.cell(0, 5, '--- END OF REPORT ---', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, 'Prepared by: Rakesh Menon, Project Manager', new_x="LMARGIN", new_y="NEXT")

    path = os.path.join(BASE, 'reports', 'status_report_q2.pdf')
    pdf.output(path)
    print(f"  [3/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 4: INVOICE (DOCX) — HAS ERROR 3
# ═══════════════════════════════════════════════════════════════
def gen_invoice():
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    doc.add_heading('TAX INVOICE', level=0)
    p = doc.add_paragraph()
    p.alignment = 1  # center
    p.add_run('Apex Construction Ltd\n').bold = True
    p.add_run('123 Industrial Layout, Bommasandra, Bengaluru 560099\n')
    p.add_run('GSTIN: 29ABCDE1234F1Z5 | PAN: ABCDE1234F')

    doc.add_paragraph()
    table = doc.add_table(rows=0, cols=2)
    table.style = 'Light List Accent 1'
    inv_meta = [
        ('Invoice No.', 'INV-2024-003'),
        ('Invoice Date', '12 August 2024'),
        ('Project', 'Greenfield Tech Park - Phase 1'),
        ('Contract Ref.', 'APEX-MPP-2024-001'),
        ('Bill To', 'Meridian Infrastructures Pvt Ltd, UB City, Vittal Mallya Road, Bengaluru 560001'),
        ('GSTIN (Customer)', '29LMNOP5678R1Z2'),
    ]
    for label, val in inv_meta:
        row = table.add_row().cells
        row[0].text = label
        row[1].text = val

    doc.add_paragraph()
    doc.add_heading('Milestone Billing', level=2)

    doc.add_paragraph(
        'This invoice is raised against the certified completion of Milestone M3 '
        '(Superstructure complete) as defined in Schedule B of the Master Project Plan. '
        'Architect certification ref: SPA/CERT/M3/2024-08 dated 9 August 2024.'
    )

    doc.add_paragraph()
    # ERROR 3: Bills Phase 3 at 100% complete, but Q2 report (July 8) said 40%
    table = doc.add_table(rows=1, cols=5)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'S.No.'
    hdr[1].text = 'Description'
    hdr[2].text = 'Phase / Milestone'
    hdr[3].text = '% Complete'
    hdr[4].text = 'Amount (Rs)'
    inv_items = [
        ('1', 'Superstructure - RCC frames, columns, slabs, beams (Floors G+14)',
         'Phase 3 / Milestone M3', '100%', '2,80,00,000'),
        ('2', 'Less: Advance already paid against this milestone',
         '', '', '0'),
    ]
    for sno, desc, phase, pct, amt in inv_items:
        row = table.add_row().cells
        row[0].text = sno
        row[1].text = desc
        row[2].text = phase
        row[3].text = pct
        row[4].text = amt

    # Subtotal
    row = table.add_row().cells
    row[3].text = 'Subtotal'
    row[4].text = '2,80,00,000'
    # GST
    row = table.add_row().cells
    row[3].text = 'GST @ 18%'
    row[4].text = '50,40,000'
    # Total
    row = table.add_row().cells
    row[3].text = 'GRAND TOTAL'
    row[4].text = '3,30,40,000'

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run('Amount in words: ').bold = True
    p.add_run('Rupees Three Crores Thirty Lakhs and Forty Thousand only.')

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run('Payment Terms: ').bold = True
    p.add_run(
        'Net 30 days from date of invoice. Payment to be made via RTGS/NEFT to the '
        'bank account details provided separately. Interest at 18% per annum applies '
        'on overdue payments.'
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run('Declaration: ').bold = True
    p.add_run(
        'We declare that this invoice reflects the true and correct value of work '
        'executed and that all materials and workmanship comply with the contract specifications.'
    )

    doc.add_paragraph()
    doc.add_paragraph('For Apex Construction Ltd')
    doc.add_paragraph()
    doc.add_paragraph('Authorised Signatory')
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run('Prepared by: ').italic = True
    p.add_run('Priya Nair, Finance Department').italic = True

    path = os.path.join(BASE, 'invoices', 'invoice_inv_2024_003.docx')
    doc.save(path)
    print(f"  [4/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 5: SITE VISIT MINUTES (TXT)
# ═══════════════════════════════════════════════════════════════
def gen_site_minutes():
    content = """\
SITE VISIT MEETING MINUTES
==========================

Date: 22 July 2024
Time: 11:00 AM to 1:30 PM
Venue: Site Office, Greenfield Tech Park, Plot 14-B, Electronic City Phase 2, Bengaluru

Attendees:
  - Vikram Rao (Sr. Project Engineer, Meridian Infrastructures - Client)
  - Rakesh Menon (Project Manager, Apex Construction - Contractor)
  - Suresh Kumar (Stores In-charge, Apex Construction)
  - Ranjit Bhalla (Site Supervisor, Apex Construction)
  - Farida Ansari (Architect's Representative, Stanton & Partners)

Minutes by: Vikram Rao, Meridian Infrastructures

--------------------------------------------------------------------

1. GENERAL PROGRESS
   The site visit covered a full walkthrough of the structure up to the 8th floor
   slab level. RCC column casting is progressing well. The general quality of
   concrete finish was noted as satisfactory, with minor honeycombing observed at
   two column locations on the 4th floor, which the Contractor agreed to rectify.

2. STEEL DELIVERY STATUS
   The Client raised concern about the steel delivery delay flagged in the Q2
   status report. The Contractor's Stores In-charge (Suresh Kumar) confirmed that
   approximately 80% of the structural steel against PO #APEX-PO-2024-029 has now
   been received at site as of the visit date. The remaining 20% is expected by
   the first week of August. The Client noted that the delay has already impacted
   the beam erection schedule for floors 6-8 and requested a revised look-ahead
   schedule within seven days.

3. SCHEDULE
   The Contractor confirmed that Phase 3 (Superstructure) is now targeted for
   completion by 25 August 2024, approximately five days ahead of the contract
   date of 31 August. The Client expressed cautious optimism but noted that this
   depends on the remaining steel arriving on time.

4. SAFETY
   One minor incident recorded in June (finger injury). Corrective action
   completed. The site safety audit conducted by the Client's team found the
   overall safety arrangements acceptable. A recommendation was made to improve
   edge protection on the 7th floor slab.

5. MEP COORDINATION
   MEP rough-in drawings were circulated for the 1st to 3rd floors. The
   Contractor requested final approval from the Architect for the 4th floor
   onwards drawings. Minor clash detection issues between HVAC duct routing and
   structural beams were noted on the 5th floor.

6. CLIENT OBSERVATIONS
   The Client noted that progress is broadly on schedule but the steel supply
   dependency remains the key risk. The Client requested weekly progress
   photographs be shared every Monday.

7. ACTION ITEMS
   a. Contractor to submit revised look-ahead schedule by 29 July 2024.
   b. Contractor to rectify honeycombing on 4th floor columns by 28 July.
   c. Architect to approve MEP drawings for 4th floor onwards by 26 July.
   d. Contractor to share weekly progress photos every Monday starting 29 July.

--------------------------------------------------------------------
Meeting closed at 1:30 PM.

Signed:
  Vikram Rao                    Rakesh Menon
  Meridian Infrastructures      Apex Construction Ltd
"""
    path = os.path.join(BASE, 'correspondence', 'site_visit_minutes_jul.txt')
    with open(path, 'w') as f:
        f.write(content)
    print(f"  [5/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 6: CONTRACT AMENDMENT (DOCX)
# ═══════════════════════════════════════════════════════════════
def gen_amendment():
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    doc.add_heading('CONTRACT AMENDMENT NO. 1', level=0)
    doc.add_heading('Greenfield Tech Park - Phase 1', level=1)

    meta = [
        ('Amendment Ref', 'APEX-MPP-2024-001-AMD-01'),
        ('Date', '30 July 2024'),
        ('Original Agreement', 'APEX-MPP-2024-001 dated 8 January 2024'),
        ('Between', 'Meridian Infrastructures Pvt Ltd ("the Employer") and Apex Construction Ltd ("the Contractor")'),
    ]
    for label, val in meta:
        p = doc.add_paragraph()
        p.add_run(f'{label}: ').bold = True
        p.add_run(val)

    doc.add_heading('Background', level=1)
    doc.add_paragraph(
        'Whereas the Contractor has experienced delays in the delivery of structural steel '
        'attributable to supplier-side production backlogs, and whereas both parties have '
        'agreed to a revised scope incorporating upgraded fire-protection cladding for the '
        'structural steel elements (required by the revised National Building Code fire '
        'safety norms, notified March 2024), the parties agree to amend the Master Project '
        'Plan as follows.'
    )

    doc.add_heading('1. Revised Contract Value', level=1)
    doc.add_paragraph(
        'The total contract value is revised from Rs 12,50,00,000 (Rupees Twelve Crores '
        'and Fifty Lakhs) to Rs 14,20,00,000 (Rupees Fourteen Crores and Twenty Lakhs). '
        'The increase of Rs 1,70,00,000 represents the cost of fire-protection cladding '
        'for all structural steel elements across floors G+14, intumescent paint for the '
        'primary load-bearing columns, and associated labour and scaffolding.'
    )

    doc.add_heading('2. Revised Project Timeline', level=1)
    doc.add_paragraph(
        'The project handover date is revised from 15 December 2024 to 31 March 2025. '
        'This extension of approximately fifteen (15) weeks accounts for the steel delivery '
        'delay (estimated impact: eight weeks) and the additional fire-protection cladding '
        'works (estimated impact: seven weeks). All phase dates in Section 5 of the Master '
        'Project Plan shall be adjusted proportionately by written notice from the Project Manager.'
    )

    doc.add_heading('3. Revised Milestone Schedule', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Light Grid Accent 1'
    hdr = table.rows[0].cells
    hdr[0].text = 'Milestone'
    hdr[1].text = 'Original Date'
    hdr[2].text = 'Revised Date'
    amd_milestones = [
        ('M1 - Site prep complete', '15 February 2024', '15 February 2024 (unchanged)'),
        ('M2 - Foundation complete', '30 April 2024', '2 May 2024'),
        ('M3 - Superstructure complete', '31 August 2024', '31 October 2024'),
        ('M4 - MEP rough-in complete', '31 October 2024', '31 December 2024'),
        ('M5 - Finishing complete', '15 December 2024', '15 March 2025'),
        ('M6 - Handover', '15 December 2024', '31 March 2025'),
    ]
    for m, orig, rev in amd_milestones:
        row = table.add_row().cells
        row[0].text = m
        row[1].text = orig
        row[2].text = rev

    doc.add_heading('4. Liquidated Damages - No Change', level=1)
    doc.add_paragraph(
        'The liquidated damages clause (Section 12 of the Master Project Plan) remains '
        'in full force and effect. The penalty rate of 0.5% of the contract value per week '
        'of delay, capped at 5% of the total (revised) contract value, shall apply to any '
        'delay beyond the revised handover date of 31 March 2025. The cap amount is revised '
        'to Rs 71,00,000 (5% of Rs 14,20,00,000).'
    )

    doc.add_heading('5. Payment Against Revised Milestones', level=1)
    doc.add_paragraph(
        'All future milestone payments shall be calculated against the revised contract value '
        'of Rs 14,20,00,000. Milestone payments already released (M1 and M2) shall not be '
        'adjusted. The revised milestone M3 payment upon superstructure completion shall be '
        '25% of the revised contract value.'
    )

    doc.add_heading('6. Fire Protection Cladding - Technical Specification', level=1)
    doc.add_paragraph(
        'All structural steel columns, beams, and trusses shall be provided with 120-minute '
        'fire-rated intumescent coating conforming to IS 15103. Application shall be carried '
        'by a certified applicator with third-party inspection by the Architect. The cost of '
        'testing and certification is included in the revised contract value.'
    )

    doc.add_heading('7. Ratification', level=1)
    doc.add_paragraph(
        'Save as expressly amended by this document, all other terms, conditions, and '
        'provisions of the Master Project Plan dated 8 January 2024 shall remain in full '
        'force and effect. This amendment shall form an integral part of the original agreement.'
    )

    doc.add_paragraph()
    doc.add_paragraph('--- END OF AMENDMENT ---')
    doc.add_paragraph()
    doc.add_paragraph('For and on behalf of Apex Construction Ltd:')
    doc.add_paragraph('______________________________')
    doc.add_paragraph('Managing Director')
    doc.add_paragraph()
    doc.add_paragraph('For and on behalf of Meridian Infrastructures Pvt Ltd:')
    doc.add_paragraph('______________________________')
    doc.add_paragraph('Director')

    path = os.path.join(BASE, 'contracts', 'contract_amendment_01.docx')
    doc.save(path)
    print(f"  [6/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 7: CLIENT COMPLAINT (TXT) — HAS ERROR 4
# ═══════════════════════════════════════════════════════════════
def gen_client_complaint():
    # ERROR 4: Client cites "15% penalty clause" - actual is 0.5%/week capped at 5%
    content = """\
From:           Anjali Deshmukh, CEO, Meridian Infrastructures Pvt Ltd
To:             Managing Director, Apex Construction Ltd
Cc:             Vikram Rao (Sr. Project Engineer, Meridian Infrastructures)
                Stanton & Partners Architects (Attn: Project Architect)
Date:           15 September 2024
Subject:        URGENT - Concerns Regarding Project Delays and Billing

Dear Sir/Madam,

I am writing to formally express our growing concern regarding the status of the
Greenfield Tech Park Phase 1 project. Despite the execution of Amendment No. 1 in
July, which extended the handover date to 31 March 2025 and increased the contract
value by Rs 1.7 crores, we are not seeing the pace of progress we expected.

Our site engineer, Mr Vikram Rao, visited the site last week and reported that
superstructure work appears to have stalled at approximately the 9th floor level.
The beam erection for floors 8 and above is significantly behind the revised
look-ahead schedule that was submitted after the July site visit. We understand
that some steel delivery issues persisted into August, but the current pace does
not reflect a contractor working to recover lost time.

Furthermore, we are deeply concerned about Invoice INV-2024-003 dated 12 August
2024, which bills Rs 2.80 crores for "Phase 3 - Superstructure 100% complete."
Based on our own site observations in August, the superstructure was nowhere near
100% complete at that time. We have asked our team to verify the Architect's
certification that supposedly confirmed this milestone, and we reserve the right
to withhold payment pending a satisfactory explanation.

We would also like to remind you that as per the 15% penalty clause in our
agreement, we are within our rights to levy substantial liquidated damages for
the cumulative delays. While we value our relationship with Apex Construction and
have been accommodating through the amendment process, we must see tangible
evidence of schedule recovery within the next two weeks, failing which we will
be compelled to consider our contractual options including termination.

Specifically, we require:
  1. A detailed explanation for Invoice INV-2024-003 and the basis on which
     Phase 3 was certified as 100% complete.
  2. A revised, credible project schedule submitted within seven (7) days.
  3. A commitment in writing to deploy additional manpower to the steel
     erection and fire-protection cladding works.
  4. A meeting between senior management of both parties within ten (10) days.

We expect a written response within five (5) working days of this letter.

This letter is sent without prejudice to our rights and remedies under the
contract and under law.

Regards,

Anjali Deshmukh
Chief Executive Officer
Meridian Infrastructures Pvt Ltd
UB City, Vittal Mallya Road, Bengaluru 560001
anjali.deshmukh@meridianinfra.in
"""
    path = os.path.join(BASE, 'correspondence', 'client_complaint_sep.txt')
    with open(path, 'w') as f:
        f.write(content)
    print(f"  [7/8] {path}")

# ═══════════════════════════════════════════════════════════════
# DOCUMENT 8: MATERIAL RECEIPT NOTE (PDF) — HAS ERROR 5
# ═══════════════════════════════════════════════════════════════
def gen_material_receipt():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'MATERIAL RECEIPT NOTE', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font('Helvetica', '', 10)
    for line in [
        'MRN No.: APEX-MRN-2024-027',
        'Date of Receipt: 20 April 2024',
        'Project: Greenfield Tech Park - Phase 1',
        'Received by: Suresh Kumar, Stores In-charge, Apex Construction Ltd',
        'Supplier: Vizag Steel Structures Pvt Ltd, Visakhapatnam',
        'Purchase Order Ref: APEX-PO-2024-029',
    ]:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'Material Details', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', 'B', 9)
    headers = ['Item', 'Spec', 'Qty', 'Unit', 'Heat/lot No.']
    widths = [55, 45, 20, 15, 45]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()
    pdf.set_font('Helvetica', '', 9)
    items = [
        ('Structural Steel ISMB 400', 'Fe500D, IS 1786', '48.500', 'MT', 'VS-2024-1187'),
        ('Structural Steel ISMB 300', 'Fe500D, IS 1786', '32.200', 'MT', 'VS-2024-1188'),
        ('Structural Steel ISMC 200', 'Fe500D, IS 1786', '18.750', 'MT', 'VS-2024-1189'),
    ]
    for item, spec, qty, unit, lot in items:
        pdf.cell(widths[0], 7, item, border=1)
        pdf.cell(widths[1], 7, spec, border=1)
        pdf.cell(widths[2], 7, qty, border=1)
        pdf.cell(widths[3], 7, unit, border=1)
        pdf.cell(widths[4], 7, lot, border=1)
        pdf.ln()

    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(widths[0], 7, 'TOTAL', border=1)
    pdf.cell(widths[1], 7, '', border=1)
    pdf.cell(widths[2], 7, '99.450', border=1)
    pdf.cell(widths[3], 7, 'MT', border=1)
    pdf.cell(widths[4], 7, '', border=1)
    pdf.ln()
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Delivery Status: COMPLETE - Delivery Lot 1 of 1 (Full Shipment)', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5,
        'The above material was received in good condition, inspected for surface '
        'defects and dimensional tolerance, and found acceptable. Material Test '
        'Certificate (MTC) from the supplier has been verified and filed. The delivery '
        'was made within the agreed PO delivery window.'
    )
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Quality Inspection', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    for line in [
        'Visual inspection: Passed. No surface defects, pitting, or rusting observed.',
        'Dimensional check: Conforming to IS 808 tolerances.',
        'MTC verified: Yield strength 545 MPa (min required 500), Elongation 14.5%.',
        'Chloride content test: Not applicable (structural steel).',
        'Inspection cleared for incorporation in works.',
    ]:
        pdf.cell(0, 5, f'  - {line}', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font('Helvetica', 'I', 9)
    pdf.cell(0, 5, 'Received and inspected by: Suresh Kumar, Stores In-charge', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, 'Witnessed by: Ranjit Bhalla, Site Supervisor', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, '--- END OF RECEIPT ---', new_x="LMARGIN", new_y="NEXT")

    path = os.path.join(BASE, 'receipts', 'material_receipt_steel.pdf')
    pdf.output(path)
    print(f"  [8/8] {path}")


# ═══════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Generating Greenfield Tech Park seed corpus...")
    gen_master_plan()
    gen_status_q1()
    gen_status_q2()
    gen_invoice()
    gen_site_minutes()
    gen_amendment()
    gen_client_complaint()
    gen_material_receipt()
    print("\nDone. All 8 documents generated.")
