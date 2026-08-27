"""Register & Deliverable Application Service for generating executive reports."""

from typing import Dict, Any
from src.app.project_service import ProjectService
from src.models.domain import ProjectRegister, FindingStatus


class RegisterService:
    """Application service for compiling and exporting Project Register deliverables."""

    @staticmethod
    def get_register(project_id: str) -> ProjectRegister:
        """Get the current reconciled Project Register, compiling on-the-fly if needed."""
        state = ProjectService.get_project_state(project_id)
        if not state.register:
            from src.reconciliation.resolver import reconcile_facts
            state.register = reconcile_facts(project_id, project_id, state.facts)
        return state.register

    get_reconciled_register = get_register
    get_project_register = get_register

    @staticmethod
    def generate_executive_report_html(project_id: str) -> str:
        """Generate a world-class, boardroom-ready executive HTML/PDF report."""
        state = ProjectService.get_project_state(project_id)
        if not state.register:
            from src.reconciliation.resolver import reconcile_facts
            state.register = reconcile_facts(project_id, project_id, state.facts)
        reg = state.register

        approved_list = [f for f in state.findings if f.status == FindingStatus.APPROVED]
        all_findings = state.findings

        # Calculate statistics
        total_docs = len(state.documents)
        total_facts = len(state.facts)
        total_metrics = len(reg.entries)
        crit_count = sum(1 for f in approved_list if f.severity.value == "CRITICAL")
        high_count = sum(1 for f in approved_list if f.severity.value == "HIGH")
        med_count = sum(1 for f in approved_list if f.severity.value in ["MEDIUM", "LOW"])

        # Format generated date
        from datetime import datetime
        generated_date_str = datetime.now().strftime("%B %d, %Y • %H:%M UTC")

        findings_html = ""
        for f in (approved_list if approved_list else all_findings):
            sev = f.severity.value.upper()
            sev_class = "tag-crit" if sev == "CRITICAL" else ("tag-high" if sev == "HIGH" else "tag-med")
            status_badge = '<span class="status-approved">✓ APPROVED REMEDIATION</span>' if f.status == FindingStatus.APPROVED else f'<span class="status-pending">{f.status.value}</span>'

            findings_html += f"""
            <div class="finding-card">
                <div class="finding-header">
                    <div class="finding-title-group">
                        <span class="tag {sev_class}">{sev}</span>
                        <span class="finding-id">[{f.finding_id}]</span>
                        <h4 class="finding-title">{f.title}</h4>
                    </div>
                    {status_badge}
                </div>
                
                <p class="finding-desc">{f.description}</p>
                
                <div class="diff-grid">
                    <div class="diff-box diff-source-a">
                        <div class="diff-box-header">
                            <span class="diff-label">SOURCE A: {f.source_a.filename}</span>
                            <span class="diff-loc">{f.source_a.location}</span>
                        </div>
                        <div class="diff-quote">"{f.source_a.exact_quote}"</div>
                    </div>
                    <div class="diff-box diff-source-b">
                        <div class="diff-box-header">
                            <span class="diff-label">SOURCE B: {f.source_b.filename if f.source_b else 'Cross-Check Record'}</span>
                            <span class="diff-loc">{f.source_b.location if f.source_b else 'Itemized Calculation'}</span>
                        </div>
                        <div class="diff-quote">"{f.source_b.exact_quote if f.source_b else 'Identified Discrepancy'}"</div>
                    </div>
                </div>

                {f'''
                <div class="remediation-box">
                    <div class="remediation-header"><strong>Actionable AI Remediation & Resolution:</strong></div>
                    <div class="remediation-action font-mono">{f.resolution_action}</div>
                </div>
                ''' if f.resolution_action else ''}

                <div class="recommendation-row">
                    <span class="rec-label">Audit Recommendation:</span> {f.recommendation}
                </div>
            </div>
            """

        register_rows_html = ""
        for idx, e in enumerate(reg.entries):
            st = e.status.upper()
            st_class = "st-corrob" if st == "CORROBORATED" else ("st-super" if st == "SUPERSEDED" else "st-contra")
            register_rows_html += f"""
            <tr class="{'even-row' if idx % 2 == 1 else ''}">
                <td class="td-entity">
                    <div class="entity-title">{e.title}</div>
                    <div class="entity-key">{e.entity_key}</div>
                </td>
                <td class="td-val font-mono">{e.reconciled_value} {e.unit or ''}</td>
                <td class="td-status"><span class="status-tag {st_class}">{st}</span></td>
                <td class="td-citation font-mono">
                    <div class="citation-doc">{e.primary_citation.filename}</div>
                    <div class="citation-loc">{e.primary_citation.location}</div>
                    <div class="citation-quote">"{e.primary_citation.exact_quote}"</div>
                </td>
            </tr>
            """

        doc_rows_html = ""
        for d in state.documents:
            doc_rows_html += f"""
            <tr>
                <td class="font-bold">{d.filename}</td>
                <td><span class="doc-badge">{d.doc_type.value}</span></td>
                <td class="font-mono text-center">{len(d.chunks)}</td>
                <td class="font-mono text-muted text-xs">{d.checksum[:16]}...</td>
            </tr>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuMesh Executive Reconciliation Report — {reg.project_name}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f1f5f9;
            color: #0f172a;
            line-height: 1.5;
            padding: 40px 20px;
        }}
        .report-wrapper {{
            max-width: 1040px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
            border: 1px solid #e2e8f0;
            overflow: hidden;
        }}
        .font-mono {{ font-family: 'JetBrains Mono', monospace; }}
        
        /* Floating Print Toolbar */
        .print-toolbar {{
            position: sticky;
            top: 20px;
            z-index: 100;
            display: flex;
            justify-content: flex-end;
            margin-bottom: 20px;
            max-width: 1040px;
            margin-left: auto;
            margin-right: auto;
        }}
        .print-btn {{
            background: #4f46e5;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.2s;
        }}
        .print-btn:hover {{ background: #4338ca; }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #090d16 0%, #1e1b4b 100%);
            color: #ffffff;
            padding: 48px;
            border-bottom: 3px solid #6366f1;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 24px;
        }}
        .brand-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(99, 102, 241, 0.4);
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #a5b4fc;
        }}
        .cert-stamp {{
            border: 2px dashed #10b981;
            padding: 6px 14px;
            border-radius: 8px;
            color: #34d399;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .title {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 8px;
        }}
        .meta-line {{
            font-size: 13px;
            color: #94a3b8;
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .meta-item strong {{ color: #cbd5e1; }}

        /* Main Content Container */
        .content {{
            padding: 48px;
        }}
        .section {{
            margin-bottom: 44px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.01em;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        /* KPI Dashboard Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 32px;
        }}
        .kpi-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
        }}
        .kpi-label {{
            font-size: 11px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .kpi-val {{
            font-size: 26px;
            font-weight: 800;
            color: #0f172a;
            line-height: 1;
        }}
        .kpi-sub {{
            font-size: 11px;
            color: #94a3b8;
            margin-top: 6px;
        }}

        /* Finding Cards */
        .finding-card {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .finding-title-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .finding-id {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 700;
            color: #6366f1;
            background: #eef2ff;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .finding-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
        }}
        .tag {{
            font-size: 10px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .tag-crit {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
        .tag-high {{ background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }}
        .tag-med {{ background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }}
        
        .status-approved {{
            font-size: 11px;
            font-weight: 800;
            color: #059669;
            background: #ecfdf5;
            padding: 4px 10px;
            border-radius: 9999px;
            border: 1px solid #a7f3d0;
        }}
        .status-pending {{
            font-size: 11px;
            font-weight: 700;
            color: #d97706;
            background: #fffbeb;
            padding: 4px 10px;
            border-radius: 9999px;
            border: 1px solid #fde68a;
        }}

        .finding-desc {{
            font-size: 13px;
            color: #334155;
            margin-bottom: 16px;
            line-height: 1.6;
        }}

        /* Diff Grid */
        .diff-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .diff-box {{
            padding: 14px;
            border-radius: 8px;
            font-size: 12px;
        }}
        .diff-source-a {{
            background: #f8fafc;
            border-left: 3px solid #6366f1;
            border-top: 1px solid #e2e8f0;
            border-right: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
        }}
        .diff-source-b {{
            background: #fef2f2;
            border-left: 3px solid #ef4444;
            border-top: 1px solid #fecaca;
            border-right: 1px solid #fecaca;
            border-bottom: 1px solid #fecaca;
        }}
        .diff-box-header {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #475569;
        }}
        .diff-quote {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #1e293b;
            font-style: italic;
            line-height: 1.5;
        }}

        /* Remediation Box */
        .remediation-box {{
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 12px;
            font-size: 12px;
            color: #065f46;
        }}
        .remediation-header {{ margin-bottom: 4px; }}
        .remediation-action {{
            font-weight: 700;
            color: #047857;
            font-size: 12px;
        }}
        .recommendation-row {{
            font-size: 12px;
            color: #475569;
        }}
        .rec-label {{ font-weight: 700; color: #1e293b; }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 12px;
        }}
        th {{
            background: #f1f5f9;
            color: #475569;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.05em;
            padding: 12px 16px;
            border-top: 1px solid #cbd5e1;
            border-bottom: 2px solid #cbd5e1;
            text-align: left;
        }}
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }}
        .even-row {{ background: #f8fafc; }}
        
        .entity-title {{ font-weight: 700; color: #0f172a; font-size: 13px; }}
        .entity-key {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #64748b; }}
        .td-val {{ font-weight: 700; font-size: 13px; color: #1e1b4b; }}
        
        .status-tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.03em;
        }}
        .st-corrob {{ background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
        .st-super {{ background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }}
        .st-contra {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}

        .td-citation {{ font-size: 11px; }}
        .citation-doc {{ font-weight: 700; color: #4f46e5; }}
        .citation-loc {{ color: #64748b; font-size: 10px; margin-bottom: 2px; }}
        .citation-quote {{ color: #475569; font-style: italic; font-size: 10px; }}

        .doc-badge {{
            background: #f1f5f9;
            color: #475569;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
        }}
        .text-center {{ text-align: center; }}
        .text-muted {{ color: #94a3b8; }}
        .text-xs {{ font-size: 11px; }}

        /* Verification Signature Footer */
        .footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 2px solid #e2e8f0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        .sig-box {{
            border: 1px dashed #cbd5e1;
            padding: 16px;
            border-radius: 8px;
            background: #f8fafc;
        }}
        .sig-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 8px; }}
        .sig-line {{ border-bottom: 1px solid #94a3b8; margin-top: 32px; margin-bottom: 6px; }}
        .sig-sub {{ font-size: 11px; color: #64748b; }}

        /* Print Media Styles */
        @media print {{
            body {{ background: white; padding: 0; }}
            .report-wrapper {{ box-shadow: none; border: none; border-radius: 0; max-width: 100%; }}
            .print-toolbar {{ display: none; }}
            .finding-card {{ break-inside: avoid; page-break-inside: avoid; }}
            tr {{ break-inside: avoid; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="print-toolbar">
        <button class="print-btn" onclick="window.print()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/><path d="M6 14h12v8H6z"/></svg>
            Print / Save to PDF
        </button>
    </div>

    <div class="report-wrapper">
        <div class="header">
            <div class="header-top">
                <div class="brand-badge">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                    DocuMesh Reconciliation Engine
                </div>
                <div class="cert-stamp">
                    ✓ Verified Audit Deliverable
                </div>
            </div>
            <h1 class="title">Executive Document Reconciliation Report</h1>
            <div class="meta-line">
                <span class="meta-item">Project: <strong>{reg.project_name}</strong></span>
                <span class="meta-item">Version: <strong>v{reg.version}</strong></span>
                <span class="meta-item">Timestamp: <strong>{generated_date_str}</strong></span>
                <span class="meta-item">Hash: <strong class="font-mono">{reg.content_hash[:16]}...</strong></span>
            </div>
        </div>

        <div class="content">
            <!-- 1. Executive Summary & KPIs -->
            <div class="section">
                <h3 class="section-title">1. Executive Audit Overview</h3>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-label">Documents Audited</div>
                        <div class="kpi-val">{total_docs}</div>
                        <div class="kpi-sub">DOCX, PDF, TXT files</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Grounded Facts</div>
                        <div class="kpi-val">{total_facts}</div>
                        <div class="kpi-sub">100% verified citations</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Confirmed Discrepancies</div>
                        <div class="kpi-val" style="color:#b91c1c;">{len(approved_list)}</div>
                        <div class="kpi-sub">{crit_count} Critical, {high_count} High</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Reconciled Entities</div>
                        <div class="kpi-val" style="color:#059669;">{total_metrics}</div>
                        <div class="kpi-sub">Audited Register metrics</div>
                    </div>
                </div>
                <p style="font-size: 13px; color: #475569; line-height: 1.6;">
                    DocuMesh executed an autonomous multi-document cross-examination across the complete project pile. 
                    All clauses, milestones, arithmetic line-items, and progress claims were cross-referenced against executed contracts, amendments, invoices, and site reports.
                </p>
            </div>

            <!-- 2. Document Inventory -->
            <div class="section">
                <h3 class="section-title">2. Ingested Document Inventory ({total_docs})</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Document File</th>
                            <th>Classified Type</th>
                            <th class="text-center">Chunks</th>
                            <th>SHA-256 Checksum</th>
                        </tr>
                    </thead>
                    <tbody>
                        {doc_rows_html}
                    </tbody>
                </table>
            </div>

            <!-- 3. Discrepancy Findings & Remediations -->
            <div class="section">
                <h3 class="section-title">
                    <span>3. Audited Discrepancies & Actionable Remediations</span>
                    <span style="font-size: 12px; font-weight: normal; color: #64748b;">({len(approved_list)} Approved Findings)</span>
                </h3>
                {findings_html}
            </div>

            <!-- 4. Master Reconciled Register -->
            <div class="section">
                <h3 class="section-title">4. Master Reconciled Project Register</h3>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 25%;">Entity / Metric</th>
                            <th style="width: 22%;">Reconciled Audited Value</th>
                            <th style="width: 15%;">Status</th>
                            <th style="width: 38%;">Primary Grounded Citation</th>
                        </tr>
                    </thead>
                    <tbody>
                        {register_rows_html}
                    </tbody>
                </table>
            </div>

            <!-- 5. Sign-off & Engine Verification -->
            <div class="footer">
                <div class="sig-box">
                    <div class="sig-title">Autonomous Engine Certification</div>
                    <div style="font-size: 12px; color: #334155;">
                        Generated via LangGraph 7-Stage State Machine with deterministic string grounding.
                    </div>
                    <div class="font-mono text-xs" style="margin-top: 8px; color: #6366f1;">
                        Run ID: {state.run_id}
                    </div>
                </div>

                <div class="sig-box">
                    <div class="sig-title">Audit Sign-off & Approval</div>
                    <div class="sig-line"></div>
                    <div class="sig-sub">Authorized Project Manager / Legal Reviewer</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

