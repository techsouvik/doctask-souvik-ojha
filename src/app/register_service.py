"""Register & Deliverable Application Service for generating executive reports."""

from typing import Dict, Any
from src.app.project_service import ProjectService
from src.models.domain import ProjectRegister, FindingStatus


class RegisterService:
    """Application service for compiling and exporting Project Register deliverables."""

    @staticmethod
    def get_register(project_id: str) -> ProjectRegister:
        """Get the current reconciled Project Register."""
        state = ProjectService.get_project_state(project_id)
        if not state.register:
            raise ValueError(f"Project Register deliverable not ready for project {project_id}. Complete Human/MCP Gate first.")
        return state.register

    @staticmethod
    def generate_executive_report_html(project_id: str) -> str:
        """Generate styled executive HTML report."""
        state = ProjectService.get_project_state(project_id)
        reg = state.register

        if not reg:
            raise ValueError(f"Register deliverable not ready for project {project_id}.")

        approved_list = [f for f in state.findings if f.status == FindingStatus.APPROVED]

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Executive Document Reconciliation Report — {reg.project_name}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #1e293b; background: #f8fafc; }}
                .header {{ background: #0f172a; color: white; padding: 24px; border-radius: 8px; margin-bottom: 30px; }}
                .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
                th {{ background: #f1f5f9; font-weight: 600; color: #475569; }}
                .tag {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; }}
                .tag-critical {{ background: #ffe4e6; color: #9f1239; }}
                .tag-high {{ background: #fef3c7; color: #92400e; }}
                .tag-medium {{ background: #e0f2fe; color: #075985; }}
                .quote {{ background: #f8fafc; border-left: 3px solid #6366f1; padding: 8px 12px; font-style: italic; font-size: 13px; font-family: monospace; margin-top: 6px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin:0;">DocuMesh Executive Reconciliation Report</h1>
                <p style="margin:5px 0 0 0; opacity:0.8;">{reg.project_name} • Version {reg.version} • Hash: {reg.content_hash}</p>
            </div>

            <div class="card">
                <h2>Executive Summary</h2>
                <p>Processed <strong>{len(state.documents)} documents</strong> across the project pile. Reconciled <strong>{len(reg.entries)} core entity metrics</strong> and identified <strong>{len(approved_list)} confirmed findings</strong> requiring management attention.</p>
            </div>

            <div class="card">
                <h2>Active Approved Findings ({len(approved_list)})</h2>
                {"".join([f'''
                    <div style="border-bottom: 1px solid #f1f5f9; padding-bottom: 15px; margin-bottom: 15px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0;">[{f.finding_id}] {f.title}</h3>
                            <span class="tag tag-{f.severity.value.lower()}">{f.severity.value}</span>
                        </div>
                        <p style="font-size:14px; color:#334155;">{f.description}</p>
                        <div class="quote"><strong>Source A ({f.source_a.filename}):</strong> "{f.source_a.exact_quote}"</div>
                        {f'<div class="quote"><strong>Source B ({f.source_b.filename}):</strong> "{f.source_b.exact_quote}"</div>' if f.source_b else ''}
                        <p style="font-size:13px; color:#4f46e5; margin-top:8px;"><strong>Recommendation:</strong> {f.recommendation}</p>
                    </div>
                ''' for f in approved_list])}
            </div>

            <div class="card">
                <h2>Reconciled Project Register</h2>
                <table>
                    <thead>
                        <tr><th>Metric</th><th>Reconciled Value</th><th>Status</th><th>Primary Source</th></tr>
                    </thead>
                    <tbody>
                        {"".join([f'''
                            <tr>
                                <td><strong>{e.title}</strong></td>
                                <td style="font-family:monospace;">{e.reconciled_value}</td>
                                <td><span class="tag">{e.status}</span></td>
                                <td>{e.primary_citation.filename} ({e.primary_citation.location})</td>
                            </tr>
                        ''' for e in reg.entries])}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
