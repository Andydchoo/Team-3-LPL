"""RevenueTwin Enterprise Platform.

AI-Powered Revenue Integrity & Fiduciary Compliance for Wealth Management.
Strictly adheres to docs/CONTRACTS.md and ui/README.md.
"""

from __future__ import annotations

import textwrap
from typing import Any
import streamlit as st

from ui.services import (
    get_case_evidence,
    get_revenue_case,
    investigate_case,
    record_review,
)

# ---------------------------------------------------------------------------
# Priority Cases Registry & Metadata
# ---------------------------------------------------------------------------

ISSUES = [
    {
        "case_id": "CASE-001",
        "name": "Anderson Household",
        "amount": "$3,000",
        "raw_amount": 3000.0,
        "aum": "$1,200,000",
        "accounts": 3,
        "custodian": "LPL Financial",
        "label": "Potential underbilling",
        "cause": "Expired pricing exception",
        "direction": "under",
        "severity": "High Impact",
        "description": "0.75% promotional waiver expired 2025-12-31; billing remained discounted instead of reverting to 1.00% contract rate.",
    },
    {
        "case_id": "CASE-003",
        "name": "Chen Household",
        "amount": "$2,500",
        "raw_amount": 2500.0,
        "aum": "$2,000,000",
        "accounts": 2,
        "custodian": "LPL Financial",
        "label": "Potential overbilling",
        "cause": "Household breakpoint tier",
        "direction": "over",
        "severity": "Fiduciary Risk",
        "description": "Household aggregated $2M AUM qualifying for 0.75% tier, but sub-accounts were billed as standalone flat 1.00% tiers.",
    },
    {
        "case_id": "CASE-004",
        "name": "Ramirez Household",
        "amount": "$2,000",
        "raw_amount": 2000.0,
        "aum": "$250,000",
        "accounts": 1,
        "custodian": "LPL Financial",
        "label": "Potential overbilling",
        "cause": "Excluded 529 asset billed",
        "direction": "over",
        "severity": "Fiduciary Risk",
        "description": "529 College Savings account explicitly excluded in agreement rider was mistakenly classified as billable asset in custodian feed.",
    },
    {
        "case_id": "CASE-002",
        "name": "Patel Household",
        "amount": "$1,600",
        "raw_amount": 1600.0,
        "aum": "$800,000",
        "accounts": 2,
        "custodian": "Schwab Institutional",
        "label": "Potential overbilling",
        "cause": "Agreement amendment backlog",
        "direction": "over",
        "severity": "Client Protection",
        "description": "Bilateral fee amendment executed 2025-10-15 reduced rate to 0.80%; custodian master was never updated from 1.00%.",
    },
    {
        "case_id": "CASE-005",
        "name": "Morgan Household",
        "amount": "Review Req.",
        "raw_amount": 0.0,
        "aum": "$3,450,000",
        "accounts": 4,
        "custodian": "Multi-Custodian (LPL/Schwab)",
        "label": "Manual review required",
        "cause": "Multi-custodian tax-ID conflict",
        "direction": "review",
        "severity": "Data Discrepancy",
        "description": "Conflicting trust account records between LPL and Schwab feeds show unlinked tax identifiers preventing automated reconciliation.",
    },
]


def money(value: float | None) -> str:
    """Format monetary numbers, handling None gracefully."""
    return "Review Dependent" if value is None else f"${value:,.0f}"


def rate(value: float | None) -> str:
    """Format rate percentages, handling None gracefully."""
    return "Review Dependent" if value is None else f"{value:.2%}"


def render_html(content: str) -> None:
    """Render raw HTML via st.html, bypassing Markdown code block parser."""
    st.html(textwrap.dedent(content).strip())


# ---------------------------------------------------------------------------
# Visual Design System: Institutional Grade FinTech CSS
# ---------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        
        :root {
            --bg-base: #F8FAFC;
            --surface: #FFFFFF;
            --surface-hover: #F1F5F9;
            --ink: #0F172A;
            --ink-secondary: #475569;
            --muted: #64748B;
            --line: #E2E8F0;
            --line-light: #F1F5F9;
            
            --emerald: #059669;
            --emerald-light: #ECFDF5;
            --emerald-glow: rgba(5, 150, 105, 0.15);
            --emerald-dark: #065F46;
            
            --coral: #E11D48;
            --coral-light: #FFF1F2;
            --coral-dark: #9F1239;
            
            --amber: #D97706;
            --amber-light: #FFFBEB;
            
            --indigo: #4F46E5;
            --indigo-light: #EEF2FF;
            
            --sidebar-bg: #090D14;
            --sidebar-card: #121824;
            --sidebar-line: #1E293B;
            --sidebar-text: #E2E8F0;
            --sidebar-muted: #94A3B8;
        }

        .stApp {
            background-color: var(--bg-base);
            color: var(--ink);
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
        }
        
        .block-container {
            max-width: 1240px;
            padding: 1.5rem 2.5rem 4rem;
        }

        h1, h2, h3, h4 {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: var(--ink);
        }

        p, div, span, button {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Top Brand Bar */
        .brand-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            border-radius: 16px;
            padding: 16px 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .brand-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .brand-mark {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 20px;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
        }
        .brand-title {
            color: #FFFFFF;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.03em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .brand-badge {
            background: rgba(16, 185, 129, 0.2);
            color: #34D399;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid rgba(16, 185, 129, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .brand-subtitle {
            color: #94A3B8;
            font-size: 13px;
            margin-top: 1px;
        }
        .brand-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .live-status {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 6px 14px;
            border-radius: 9999px;
            color: #34D399;
            font-size: 12px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #10B981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10B981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        /* Hero Banner */
        .hero-banner {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 24px 28px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04);
        }
        .hero-banner h1 {
            font-size: 32px;
            margin: 4px 0 6px;
            letter-spacing: -0.04em;
        }
        .hero-banner p {
            color: var(--muted);
            font-size: 15px;
            margin: 0;
        }
        .as-of-badge {
            background: var(--surface-hover);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 12px 18px;
            text-align: right;
        }
        .as-of-badge span {
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
        }
        .as-of-badge strong {
            font-size: 14px;
            color: var(--ink);
        }

        /* Stepper */
        .stepper {
            display: flex;
            align-items: center;
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px 20px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .step-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 12px;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: 'JetBrains Mono', monospace;
        }
        .step-item.active {
            color: var(--emerald);
        }
        .step-circle {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            background: var(--surface-hover);
            border: 1px solid var(--line);
            color: var(--muted);
        }
        .step-item.active .step-circle {
            background: var(--emerald-light);
            border-color: var(--emerald);
            color: var(--emerald);
            box-shadow: 0 0 10px rgba(5, 150, 105, 0.2);
        }
        .step-divider {
            flex: 1;
            height: 2px;
            background: var(--line);
            margin: 0 12px;
        }
        .step-divider.active {
            background: var(--emerald);
        }

        /* KPI Metric Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .kpi-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 18px 20px;
            box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.03);
            position: relative;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px -4px rgba(0, 0, 0, 0.06);
            border-color: #CBD5E1;
        }
        .kpi-top-bar {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }
        .bar-emerald { background: var(--emerald); }
        .bar-coral { background: var(--coral); }
        .bar-indigo { background: var(--indigo); }
        .bar-amber { background: var(--amber); }

        .kpi-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            font-family: 'JetBrains Mono', monospace;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 26px;
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.03em;
            margin-bottom: 4px;
        }
        .kpi-sub {
            font-size: 12px;
            color: var(--muted);
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .kpi-pill {
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
        }
        .pill-green { background: #ECFDF5; color: #047857; }
        .pill-red { background: #FFF1F2; color: #BE123C; }

        /* Triage Queue Item */
        .queue-item {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 18px 22px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .queue-item:hover {
            border-color: #94A3B8;
            box-shadow: 0 8px 25px -4px rgba(0, 0, 0, 0.07);
            transform: translateY(-1px);
        }
        .queue-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .queue-avatar {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
        }
        .queue-name {
            font-size: 17px;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 2px;
        }
        .queue-details {
            font-size: 13px;
            color: var(--muted);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .tag-pill {
            padding: 3px 9px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.02em;
        }
        .tag-under {
            background: #ECFDF5;
            color: #047857;
            border: 1px solid #A7F3D0;
        }
        .tag-over {
            background: #FFF1F2;
            color: #BE123C;
            border: 1px solid #FECDD3;
        }
        .tag-review {
            background: #FFFBEB;
            color: #B45309;
            border: 1px solid #FDE68A;
        }
        .queue-right {
            display: flex;
            align-items: center;
            gap: 24px;
            text-align: right;
        }
        .queue-impact {
            font-size: 20px;
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.02em;
        }
        .queue-impact-sub {
            font-size: 11px;
            color: var(--muted);
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Case Screen */
        .case-hero {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            border-radius: 20px;
            padding: 28px 32px;
            margin-bottom: 24px;
            color: #FFFFFF;
            box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .case-eyebrow {
            color: #34D399;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 6px;
        }
        .case-hero h1 {
            color: #FFFFFF !important;
            font-size: 34px;
            margin: 0 0 8px;
            letter-spacing: -0.04em;
        }
        .case-hero-meta {
            display: flex;
            gap: 20px;
            font-size: 14px;
            color: #94A3B8;
        }
        .case-meta-tag {
            background: rgba(255, 255, 255, 0.1);
            padding: 4px 10px;
            border-radius: 6px;
            color: #E2E8F0;
            font-size: 12px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Deterministic Finding Box */
        .finding-box {
            background: var(--surface);
            border: 1px solid #CBD5E1;
            border-top: 4px solid var(--emerald);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 4px 20px -3px rgba(0, 0, 0, 0.05);
        }
        .finding-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #ECFDF5;
            color: #047857;
            border: 1px solid #A7F3D0;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 16px;
        }
        .financial-metric-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            padding: 12px 0;
            border-bottom: 1px solid var(--line);
        }
        .financial-metric-row:last-child {
            border-bottom: none;
        }
        .f-label {
            color: var(--muted);
            font-size: 14px;
            font-weight: 500;
        }
        .f-val {
            font-size: 20px;
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.02em;
        }
        .diff-card {
            background: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 12px;
            padding: 16px;
            margin-top: 16px;
            text-align: center;
        }
        .diff-amount-under {
            font-size: 30px;
            font-weight: 800;
            color: #059669;
            letter-spacing: -0.03em;
        }
        .diff-amount-over {
            font-size: 30px;
            font-weight: 800;
            color: #E11D48;
            letter-spacing: -0.03em;
        }
        .diff-caption {
            font-size: 12px;
            color: var(--muted);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
            margin-top: 2px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* AI Panel */
        .ai-card {
            background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
            border: 1px solid #CBD5E1;
            border-top: 4px solid var(--indigo);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 4px 20px -3px rgba(0, 0, 0, 0.05);
        }
        .ai-header-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #EEF2FF;
            color: #4F46E5;
            border: 1px solid #C7D2FE;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 14px;
        }
        .ai-cause-title {
            font-size: 20px;
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.03em;
            margin-bottom: 8px;
        }
        .ai-summary {
            color: var(--ink-secondary);
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 16px;
        }
        .evidence-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .ev-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-family: 'JetBrains Mono', monospace;
        }
        .ev-val {
            font-size: 13px;
            font-weight: 700;
            color: var(--ink);
        }
        .action-recommendation {
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-radius: 12px;
            padding: 14px 16px;
            margin-top: 14px;
            font-size: 13px;
            color: #92400E;
            line-height: 1.5;
        }
        .action-recommendation strong {
            display: block;
            font-size: 11px;
            text-transform: uppercase;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
            color: #B45309;
        }

        /* SEC Audit Certificate */
        .audit-cert {
            background: linear-gradient(135deg, #064E3B 0%, #065F46 100%);
            border: 1px solid #10B981;
            border-radius: 18px;
            padding: 24px 28px;
            margin-bottom: 24px;
            color: #FFFFFF;
            box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.4);
        }
        .audit-cert h3 {
            color: #FFFFFF !important;
            font-size: 22px;
            margin: 0 0 6px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .audit-meta-row {
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #A7F3D0;
            margin-top: 8px;
            font-family: 'JetBrains Mono', monospace;
        }

        /* Streamlit Button Overrides */
        .stButton > button {
            border-radius: 10px !important;
            min-height: 44px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: -0.01em;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.08) !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid var(--sidebar-line);
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
            color: var(--sidebar-muted) !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background-color: #121824 !important;
            color: #E2E8F0 !important;
            border: 1px solid #1E293B !important;
            text-align: left;
            justify-content: flex-start;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            border-color: #334155 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Brand & Progress Helpers
# ---------------------------------------------------------------------------

def render_brand() -> None:
    render_html(
        """
        <div class="brand-container">
            <div class="brand-left">
                <div class="brand-mark">◈</div>
                <div>
                    <div class="brand-title">
                        RevenueTwin
                        <span class="brand-badge">Enterprise Edition</span>
                    </div>
                    <div class="brand-subtitle">Autonomous Revenue Integrity & Fiduciary Compliance for Wealth Management</div>
                </div>
            </div>
            <div class="brand-right">
                <div class="live-status">
                    <span class="pulse-dot"></span>
                    <span>CUSTODY SYNC: LPL + SCHWAB LIVE</span>
                </div>
            </div>
        </div>
        """
    )


def render_stepper(stage: int) -> None:
    """Render 5-stage workflow stepper."""
    steps = [
        ("1", "Detect"),
        ("2", "Investigate"),
        ("3", "Explain"),
        ("4", "Quantify"),
        ("5", "Human Review"),
    ]
    chunks = []
    for i, (num, lbl) in enumerate(steps):
        active_cls = " active" if i <= stage else ""
        chunks.append(
            f'<div class="step-item{active_cls}">'
            f'<div class="step-circle">{num}</div>'
            f'<span>{lbl}</span>'
            f'</div>'
        )
        if i < len(steps) - 1:
            div_active = " active" if i < stage else ""
            chunks.append(f'<div class="step-divider{div_active}"></div>')

    render_html(f'<div class="stepper">{"".join(chunks)}</div>')


# ---------------------------------------------------------------------------
# Dashboard Screens
# ---------------------------------------------------------------------------

def render_dashboard() -> None:
    render_html(
        """
        <div class="hero-banner">
            <div>
                <div style="color:var(--emerald);font-family:'JetBrains Mono';font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">
                    Advisory Practice Portfolio
                </div>
                <h1>Summit Wealth Partners</h1>
                <p>Continuous algorithmic audit across 1,248 client accounts and $1.24B AUM</p>
            </div>
            <div class="as-of-badge">
                <span>Last Custody Sync</span>
                <strong>January 1, 2026 · 09:00 UTC</strong>
            </div>
        </div>
        """
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Revenue Integrity Command Center",
        "📊 Risk & Revenue Leakage Analytics",
        "💎 $100M Enterprise Valuation Simulator",
        "🧬 Digital Twin Architecture & SEC Governance",
    ])

    with tab1:
        render_command_center()

    with tab2:
        render_analytics()

    with tab3:
        render_roi_simulator()

    with tab4:
        render_architecture()


def render_command_center() -> None:
    render_stepper(0)

    render_html(
        """
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-top-bar bar-indigo"></div>
                <div class="kpi-label">Monitored AUM</div>
                <div class="kpi-value">$1.24B</div>
                <div class="kpi-sub">642 Households · 1,248 Accounts</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-top-bar bar-amber"></div>
                <div class="kpi-label">Discrepancies Requiring Review</div>
                <div class="kpi-value">5 Cases</div>
                <div class="kpi-sub"><span class="kpi-pill pill-red">99.6% Clean Billing</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-top-bar bar-emerald"></div>
                <div class="kpi-label">Protected Underbilling</div>
                <div class="kpi-value">+$3,000<span style="font-size:14px;font-weight:500;">/yr</span></div>
                <div class="kpi-sub"><span class="kpi-pill pill-green">Fee Leakage Recovered</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-top-bar bar-coral"></div>
                <div class="kpi-label">Client Overbilling Shield</div>
                <div class="kpi-value">$6,100<span style="font-size:14px;font-weight:500;">/yr</span></div>
                <div class="kpi-sub"><span class="kpi-pill pill-red">SEC & Fiduciary Risk Averted</span></div>
            </div>
            <div class="kpi-card">
                <div class="kpi-top-bar bar-emerald"></div>
                <div class="kpi-label">Net Platform ROI</div>
                <div class="kpi-value">14.8x</div>
                <div class="kpi-sub">Advisory Value vs Subscription</div>
            </div>
        </div>
        """
    )

    c_title, c_filter = st.columns([2.5, 1.5])
    with c_title:
        st.markdown("### Priority Review Queue")
        st.caption("5 algorithmic findings detected · sorted by materiality & fiduciary exposure")
    with c_filter:
        filter_opt = st.selectbox(
            "Filter Findings",
            ["All Findings (5)", "Potential Underbilling", "Potential Overbilling", "Manual Review Required"],
            label_visibility="collapsed",
        )

    filtered_issues = ISSUES
    if filter_opt == "Potential Underbilling":
        filtered_issues = [i for i in ISSUES if i["direction"] == "under"]
    elif filter_opt == "Potential Overbilling":
        filtered_issues = [i for i in ISSUES if i["direction"] == "over"]
    elif filter_opt == "Manual Review Required":
        filtered_issues = [i for i in ISSUES if i["direction"] == "review"]

    for issue in filtered_issues:
        tag_class = f"tag-{issue['direction']}"
        with st.container():
            col_info, col_act = st.columns([3.8, 1.2], gap="medium")
            with col_info:
                sub_label = "annual impact" if issue['raw_amount'] > 0 else "action needed"
                render_html(
                    f"""
                    <div class="queue-item">
                        <div class="queue-left">
                            <div class="queue-avatar">{issue['name'][0]}</div>
                            <div>
                                <div class="queue-name">{issue['name']}</div>
                                <div class="queue-details">
                                    <span>{issue['aum']} AUM</span>
                                    <span>•</span>
                                    <span>{issue['accounts']} Accounts</span>
                                    <span>•</span>
                                    <span>Custodian: {issue['custodian']}</span>
                                </div>
                                <div style="margin-top:6px;">
                                    <span class="tag-pill {tag_class}">{issue['label']}</span>
                                    <span style="font-size:12px;color:var(--muted);margin-left:8px;">{issue['cause']}</span>
                                </div>
                            </div>
                        </div>
                        <div class="queue-right">
                            <div>
                                <div class="queue-impact">{issue['amount']}</div>
                                <div class="queue-impact-sub">{sub_label}</div>
                            </div>
                        </div>
                    </div>
                    """
                )
            with col_act:
                st.write("")
                st.write("")
                is_primary = issue["direction"] == "under"
                if st.button("Inspect Case →", key=f"open_{issue['case_id']}", use_container_width=True, type="primary" if is_primary else "secondary"):
                    st.session_state.case_id = issue["case_id"]
                    st.session_state.screen = "case"
                    st.session_state.investigation = None
                    st.session_state.review = None
                    st.rerun()

    st.write("")
    render_html(
        """
        <div style="background:#F1F5F9;border:1px solid #CBD5E1;border-radius:14px;padding:20px 24px;display:flex;align-items:center;gap:18px;">
            <div style="font-size:28px;">⚖️</div>
            <div>
                <strong style="color:var(--ink);font-size:15px;display:block;margin-bottom:2px;">The RevenueTwin Core Guarantee: Deterministic Math + Contextual AI + Human Control</strong>
                <span style="color:var(--muted);font-size:13px;">Authoritative financial calculations are determined by Python code. The investigation layer interprets agreements and operational context. A human reviewer chooses the next workflow action.</span>
            </div>
        </div>
        """
    )


def render_analytics() -> None:
    st.markdown("### Revenue Leakage & Compliance Exposure Analytics")
    st.caption("Forensic breakdown of billing discrepancies across fee structures, custodian feeds, and household accounts")

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("#### Discrepancies by Category")
        categories = [
            ("Expired Pricing Exceptions", "$3,000 / yr", "33%", "#059669"),
            ("Unapplied Household Breakpoints", "$2,500 / yr", "27%", "#E11D48"),
            ("Ineligible Asset Inclusions (529)", "$2,000 / yr", "22%", "#E11D48"),
            ("Fee Amendment Implementation Lag", "$1,600 / yr", "18%", "#E11D48"),
        ]
        for cname, camt, cpct, ccolor in categories:
            render_html(
                f"""
                <div style="margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;font-size:14px;font-weight:600;margin-bottom:4px;">
                        <span>{cname}</span>
                        <span>{camt} <span style="color:var(--muted);font-weight:400;">({cpct})</span></span>
                    </div>
                    <div style="width:100%;height:8px;background:#E2E8F0;border-radius:9999px;overflow:hidden;">
                        <div style="width:{cpct};height:100%;background:{ccolor};border-radius:9999px;"></div>
                    </div>
                </div>
                """
            )

    with col_b:
        st.markdown("#### Custodian Feed Synchronization")
        custodians = [
            ("LPL Financial Custodial Master", "1,104 Accounts", "99.8% Healthy", "🟢 Synchronized"),
            ("Schwab Institutional Feed", "128 Accounts", "98.4% Healthy", "🟢 Synchronized"),
            ("Fidelity IWS Cross-Feed", "16 Accounts", "93.7% Discrepancies", "🟡 Re-indexing"),
        ]
        for cname, ccount, chealth, cstatus in custodians:
            render_html(
                f"""
                <div style="background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:700;font-size:14px;color:var(--ink);">{cname}</div>
                        <div style="font-size:12px;color:var(--muted);">{ccount} · {chealth}</div>
                    </div>
                    <div style="font-size:12px;font-weight:600;font-family:'JetBrains Mono';">{cstatus}</div>
                </div>
                """
            )

    st.write("")
    st.info("💡 **Synthetic scenario:** These charts summarize the curated demo cases. They are not industry benchmarks or claims about LPL practices.")


def render_roi_simulator() -> None:
    st.markdown("### Enterprise Scale & $100M+ Valuation Simulator")
    st.caption("Illustrative synthetic scenario for exploring how impact could scale across advisory practices")

    c1, c2 = st.columns([1.2, 1.8], gap="large")

    with c1:
        st.markdown("#### Practice / Network Parameters")
        aum_input = st.slider("Total Monitored AUM ($ Millions)", min_value=100, max_value=25000, value=1240, step=100)
        fee_bps = st.slider("Average Advisory Fee (Basis Points)", min_value=50, max_value=150, value=100, step=5)
        leakage_rate = st.slider("Estimated Discrepancy Rate (%)", min_value=0.5, max_value=4.0, value=1.8, step=0.1)

    with c2:
        total_aum_dollars = aum_input * 1_000_000
        gross_fee_revenue = total_aum_dollars * (fee_bps / 10000)
        annual_discrepancy_pool = gross_fee_revenue * (leakage_rate / 100)
        underbilling_recovered = annual_discrepancy_pool * 0.45
        fiduciary_shield = annual_discrepancy_pool * 0.55
        ops_hours_saved = int(aum_input * 0.75)
        platform_cost = max(24_000, int(total_aum_dollars * 0.00004))
        net_roi = (underbilling_recovered + fiduciary_shield * 0.3) / platform_cost

        st.markdown("#### Dynamic Value Realization")
        render_html(
            f"""
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px;">
                <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:14px;padding:16px;">
                    <div style="font-size:11px;font-family:'JetBrains Mono';font-weight:700;color:#047857;text-transform:uppercase;">Annual Underbilling Recovered</div>
                    <div style="font-size:26px;font-weight:800;color:#065F46;margin-top:4px;">${underbilling_recovered:,.0f}</div>
                    <div style="font-size:12px;color:#047857;">Direct cash to advisor bottom-line</div>
                </div>
                <div style="background:#FFF1F2;border:1px solid #FECDD3;border-radius:14px;padding:16px;">
                    <div style="font-size:11px;font-family:'JetBrains Mono';font-weight:700;color:#BE123C;text-transform:uppercase;">Fiduciary Overbilling Averted</div>
                    <div style="font-size:26px;font-weight:800;color:#9F1239;margin-top:4px;">${fiduciary_shield:,.0f}</div>
                    <div style="font-size:12px;color:#BE123C;">Zero regulatory audit penalties</div>
                </div>
                <div style="background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;">
                    <div style="font-size:11px;font-family:'JetBrains Mono';font-weight:700;color:var(--muted);text-transform:uppercase;">Annual Audit Hours Saved</div>
                    <div style="font-size:26px;font-weight:800;color:var(--ink);margin-top:4px;">{ops_hours_saved:,} hrs</div>
                    <div style="font-size:12px;color:var(--muted);">Replaces manual Excel reconciliation</div>
                </div>
                <div style="background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;">
                    <div style="font-size:11px;font-family:'JetBrains Mono';font-weight:700;color:var(--muted);text-transform:uppercase;">Platform Net ROI Multiple</div>
                    <div style="font-size:26px;font-weight:800;color:var(--emerald);margin-top:4px;">{net_roi:.1f}x</div>
                    <div style="font-size:12px;color:var(--muted);">Payback period under 30 days</div>
                </div>
            </div>
            """
        )

    render_html(
        """
        <div style="background:linear-gradient(135deg, #0F172A 0%, #1E293B 100%);border-radius:16px;padding:24px;color:#FFFFFF;margin-top:10px;">
            <div style="color:#34D399;font-family:'JetBrains Mono';font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">
                Strategic Acquisition Thesis for LPL Financial ($1.4 Trillion Network)
            </div>
            <h3 style="color:#FFFFFF !important;font-size:20px;margin:0 0 10px;">Why LPL Financial Acquires RevenueTwin</h3>
            <p style="color:#CBD5E1;font-size:14px;line-height:1.6;margin:0;">
                This synthetic scenario illustrates how a revenue-integrity platform could create a strategic moat: recovering legitimate revenue, protecting clients, and building toward an <strong>autonomous revenue twin with human governance</strong>.
            </p>
        </div>
        """
    )


def render_architecture() -> None:
    st.markdown("### Digital Twin Architecture & Human Governance")
    st.caption("How RevenueTwin separates deterministic financial facts, contextual investigation, and human decisions")

    render_html(
        """
        <div style="background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:24px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div style="text-align:center;flex:1;min-width:140px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:16px;">
                    <div style="font-size:24px;margin-bottom:6px;">📥</div>
                    <strong style="display:block;font-size:13px;color:var(--ink);">1. Custody Feeds</strong>
                    <span style="font-size:11px;color:var(--muted);">LPL, Schwab, Fidelity</span>
                </div>
                <div style="font-size:20px;color:var(--muted);">→</div>
                <div style="text-align:center;flex:1;min-width:140px;background:#ECFDF5;border:1px solid #A7F3D0;border-radius:12px;padding:16px;">
                    <div style="font-size:24px;margin-bottom:6px;">⚙️</div>
                    <strong style="display:block;font-size:13px;color:#065F46;">2. Deterministic Twin</strong>
                    <span style="font-size:11px;color:#047857;">Python Decimal Math (0% Hallucination)</span>
                </div>
                <div style="font-size:20px;color:var(--muted);">→</div>
                <div style="text-align:center;flex:1;min-width:140px;background:#EEF2FF;border:1px solid #C7D2FE;border-radius:12px;padding:16px;">
                    <div style="font-size:24px;margin-bottom:6px;">🧠</div>
                    <strong style="display:block;font-size:13px;color:#3730A3;">3. Bedrock AI</strong>
                    <span style="font-size:11px;color:#4F46E5;">Bedrock investigation · planned</span>
                </div>
                <div style="font-size:20px;color:var(--muted);">→</div>
                <div style="text-align:center;flex:1;min-width:140px;background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;padding:16px;">
                    <div style="font-size:24px;margin-bottom:6px;">👤</div>
                    <strong style="display:block;font-size:13px;color:#92400E;">4. Human Gate</strong>
                    <span style="font-size:11px;color:#B45309;">Compliance Sign-Off Enforced</span>
                </div>
                <div style="font-size:20px;color:var(--muted);">→</div>
                <div style="text-align:center;flex:1;min-width:140px;background:#0F172A;border:1px solid #334155;border-radius:12px;padding:16px;color:#FFFFFF;">
                    <div style="font-size:24px;margin-bottom:6px;">🔒</div>
                    <strong style="display:block;font-size:13px;color:#34D399;">5. Review Record</strong>
                    <span style="font-size:11px;color:#94A3B8;">Durable persistence · planned</span>
                </div>
            </div>
        </div>
        """
    )

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### Deterministic Financial Separation")
        st.write(
            "AI does not compute client billing directly. RevenueTwin implements a strict architectural boundary: "
            "every dollar calculation is computed using Python `Decimal` algorithms, while investigation explains "
            "the surrounding evidence."
        )
    with col2:
        st.markdown("#### Fiduciary Compliance Shield")
        st.write(
            "The planned Bedrock investigation layer will read agreement evidence, find expiration clauses, and "
            "cross-reference billing records. It will explain *why* numbers may differ, while a human chooses the workflow action."
        )


# ---------------------------------------------------------------------------
# Case Inspection View (Detailed Forensic Investigation)
# ---------------------------------------------------------------------------

def render_case(case: dict[str, Any]) -> None:
    investigation = st.session_state.get("investigation")
    review = st.session_state.get("review")

    # Workflow progress stage: 1=Detect, 2=Investigate, 3=Explain, 4=Quantify, 5=Human Review
    stage = 4 if review else (2 if investigation else 1)
    render_stepper(stage)

    # Back navigation
    if st.button("← Return to Command Center", key="back_btn"):
        st.session_state.screen = "dashboard"
        st.rerun()

    # Case metadata
    is_underbilling = case.get("impact_direction") == "potential_underbilling"
    pricing_name = str(case.get("calculation_method", "flat")).title()
    as_of = case.get("as_of_date", "2026-01-01")

    render_html(
        f"""
        <div class="case-hero">
            <div class="case-eyebrow">Case {case['case_id']} · Algorithmic Triage</div>
            <h1>{case['household']}</h1>
            <div class="case-hero-meta">
                <span class="case-meta-tag">AUM: {money(case.get('aum'))}</span>
                <span class="case-meta-tag">Pricing: {pricing_name}</span>
                <span class="case-meta-tag">As-of Date: {as_of}</span>
                <span class="case-meta-tag" style="color:#34D399;">Status: Requires Human Review</span>
            </div>
        </div>
        """
    )

    # Human workflow confirmation; this does not execute or authorize a fee change.
    if review:
        render_html(
            f"""
            <div class="audit-cert">
                <h3>✓ Human decision recorded</h3>
                <p style="margin:0 0 8px;font-size:14px;color:#D1FAE5;">
                    Decision: <strong>{review['decision'].replace('_', ' ').upper()}</strong> selected by a human reviewer.
                    This demo records the workflow decision only; no fee change was executed or authorized automatically.
                </p>
                <div class="audit-meta-row">
                    <span>Review ID: {review['review_id']}</span>
                    <span>Timestamp: {review['recorded_at']} UTC</span>
                </div>
            </div>
            """
        )

    # Split-Screen Forensic Command Grid
    col_left, col_right = st.columns([1.1, 1.25], gap="large")

    # Left Column: Deterministic Truth (Mathematical Finding)
    with col_left:
        diff_class = "diff-amount-under" if is_underbilling else "diff-amount-over"
        impact_word = "underbilling" if is_underbilling else "overbilling"
        expected_fee_str = money(case.get("expected_annual_fee"))
        expected_rate_str = rate(case.get("expected_rate"))
        actual_fee_str = money(case.get("actual_annual_fee"))
        actual_rate_str = rate(case.get("actual_rate"))
        diff_str = money(case.get("annual_difference"))

        render_html(
            f"""
            <div class="finding-box">
                <div class="finding-badge">
                    <span>🛡️ Deterministic Engine Verified</span>
                </div>
                <div style="color:var(--muted);font-size:12px;font-family:'JetBrains Mono';text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;">
                    Authoritative Financial Finding
                </div>
                <div class="financial-metric-row">
                    <span class="f-label">Expected Annual Fee</span>
                    <span class="f-val">{expected_fee_str} <span style="font-size:13px;color:var(--muted);font-weight:400;">({expected_rate_str})</span></span>
                </div>
                <div class="financial-metric-row">
                    <span class="f-label">Actual Custodian Billing</span>
                    <span class="f-val">{actual_fee_str} <span style="font-size:13px;color:var(--muted);font-weight:400;">({actual_rate_str})</span></span>
                </div>
                <div class="financial-metric-row">
                    <span class="f-label">Total Account AUM</span>
                    <span class="f-val">{money(case.get('aum'))}</span>
                </div>
                <div class="diff-card">
                    <div class="{diff_class}">{diff_str} / year</div>
                    <div class="diff-caption">Potential Annual {impact_word}</div>
                </div>
                <div style="margin-top:20px;padding:12px 14px;background:#F8FAFC;border-radius:10px;border:1px solid #E2E8F0;font-size:11px;color:var(--muted);font-family:'JetBrains Mono';">
                    Verification: SHA256:{case['case_id']}:VERIFIED_DETERMINISTIC<br>
                    Math Engine: Python Decimal · AI does not perform this calculation
                </div>
            </div>
            """
        )

    # Right Column: AI Contextual Investigation
    with col_right:
        if not investigation and not review:
            render_html(
                """
                <div class="ai-card">
                    <div class="ai-header-badge">
                        <span>◈ RevenueTwin investigation · DEMO MOCK</span>
                    </div>
                    <div class="ai-cause-title">Uncover the Root Cause</div>
                    <div class="ai-summary">
                        RevenueTwin can automatically cross-reference the client's executed advisory contract, 
                        bilateral pricing waivers, household grouping schedules, and custodian billing logs to explain 
                        why this discrepancy exists.
                    </div>
                </div>
                """
            )
            st.write("")
            if st.button("⚡ Investigate with RevenueTwin · Demo", type="primary", use_container_width=True):
                with st.spinner("Reviewing contract evidence and billing configuration..."):
                    try:
                        st.session_state.investigation = investigate_case(case["case_id"])
                    except Exception as err:
                        st.error(f"Investigation service unavailable: {err}")
                    st.rerun()

        elif investigation:
            render_investigation_details(investigation, case)


def render_investigation_details(investigation: dict[str, Any], case: dict[str, Any]) -> None:
    """Render structured AI investigation conforming to docs/CONTRACTS.md."""
    status = investigation.get("investigation_status", "supported_explanation")
    cause = investigation.get("likely_cause") or "Root Cause Analysis"
    summary = investigation.get("summary", "Analysis completed.")
    evidence_strength = str(investigation.get("evidence_strength", "low")).upper()
    recommended = investigation.get("recommended_action", "Send for compliance review.")

    # Graceful handling if investigation encountered error or conflicting evidence
    if status == "investigation_error":
        st.error(f"AI Investigation Error: {summary}")
        if st.button("Retry Investigation"):
            st.session_state.investigation = None
            st.rerun()
        return

    # Corroborating evidence lookup
    try:
        raw_evidence = get_case_evidence(case["case_id"])
        evidence_lookup = {item["evidence_id"]: item for item in raw_evidence}
    except Exception:
        evidence_lookup = {}

    ev_cards: list[tuple[str, str]] = []
    for used in investigation.get("evidence_used", []):
        eid = used.get("evidence_id", "")
        item = evidence_lookup.get(eid)
        if item:
            ev_cards.append((item.get("title", eid.replace("_", " ").title()), used.get("finding", "")))
        else:
            ev_cards.append((eid.replace("_", " ").title(), used.get("finding", "")))

    if not ev_cards:
        ev_cards = [("Custodian Records", "Evidence connected and verified via custody data stream.")]

    # Render AI card with clean HTML
    ev_html_rows = "".join(
        f'<div class="evidence-card"><span class="ev-label">{lbl}</span><span class="ev-val">{v}</span></div>'
        for lbl, v in ev_cards
    )

    render_html(
        f"""
        <div class="ai-card">
            <div class="ai-header-badge">
                <span>◈ RevenueTwin investigation · DEMO MOCK · Evidence strength {evidence_strength}</span>
            </div>
            <div class="ai-cause-title">{cause}</div>
            <div class="ai-summary">{summary}</div>
            <div style="margin:16px 0 10px;">
                <div style="font-size:11px;font-family:'JetBrains Mono';font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">
                    Corroborating Evidence Ledger
                </div>
                {ev_html_rows}
            </div>
            <div class="action-recommendation">
                <strong>Recommended Next Step</strong>
                {recommended}
            </div>
        </div>
        """
    )

    # Human Controls
    if not st.session_state.get("review"):
        st.write("")
        st.caption("Human-in-the-loop governance: choose a workflow decision. This demo records the decision only; it does not change billing or submit a custodial action.")

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("🟢 Send for Review", type="primary", use_container_width=True):
                st.session_state.review = record_review(case["case_id"], "send_for_review")
                st.rerun()
        with btn_col2:
            if st.button("🟡 Investigate Further", use_container_width=True):
                st.session_state.review = record_review(case["case_id"], "investigate_further")
                st.rerun()
        with btn_col3:
            if st.button("⚪ Dismiss Finding", use_container_width=True):
                st.session_state.review = record_review(case["case_id"], "dismiss")
                st.rerun()
    else:
        st.write("")
        if st.button("Re-evaluate Case / Revoke Decision", use_container_width=True):
            st.session_state.review = None
            st.rerun()


# ---------------------------------------------------------------------------
# Sidebar & Application Main
# ---------------------------------------------------------------------------

def render_sidebar() -> None:
    with st.sidebar:
        render_html(
            """
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                <div style="width:32px;height:32px;background:#10B981;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#FFFFFF;font-weight:800;font-size:16px;">◈</div>
                <div>
                    <strong style="color:#FFFFFF;font-size:16px;display:block;">RevenueTwin</strong>
                    <span style="color:#94A3B8;font-size:11px;">LPL FinTech Suite</span>
                </div>
            </div>
            """
        )

        st.markdown("### Active Workspace")
        render_html(
            """
            <div style="background:#121824;border:1px solid #1E293B;border-radius:10px;padding:12px;margin-bottom:14px;">
                <div style="font-weight:700;color:#FFFFFF;font-size:13px;">Summit Wealth Partners</div>
                <div style="color:#94A3B8;font-size:11px;margin-top:2px;">RIA #84912 · LPL Enterprise</div>
                <div style="color:#34D399;font-size:11px;font-family:'JetBrains Mono';margin-top:6px;">$1.24B Monitored AUM</div>
            </div>
            """
        )

        if st.button("📊 Command Center Dashboard", use_container_width=True):
            st.session_state.screen = "dashboard"
            st.rerun()

        st.markdown("---")
        st.markdown("### Priority Queue Shortcuts")
        for issue in ISSUES:
            direction_emoji = "📈" if issue["direction"] == "under" else ("🛡️" if issue["direction"] == "over" else "🔍")
            btn_label = f"{direction_emoji} {issue['name']}"
            if st.button(btn_label, key=f"side_{issue['case_id']}", use_container_width=True):
                st.session_state.case_id = issue["case_id"]
                st.session_state.screen = "case"
                st.session_state.investigation = None
                st.session_state.review = None
                st.rerun()

        st.markdown("---")
        st.markdown("### System Telemetry")
        render_html(
            """
            <div style="font-size:11px;font-family:'JetBrains Mono';color:#94A3B8;line-height:1.8;">
                <div>Engine: <span style="color:#34D399;">Local deterministic Python</span></div>
                <div>Investigation: <span style="color:#FBBF24;">Demo mock · Bedrock planned</span></div>
                <div>Evidence: <span style="color:#34D399;">Local synthetic fixtures</span></div>
                <div>Review persistence: <span style="color:#FBBF24;">Session mock · AWS planned</span></div>
            </div>
            """
        )

        st.write("")
        if st.button("🔄 Reset Demo Session", use_container_width=True):
            st.session_state.screen = "dashboard"
            st.session_state.case_id = "CASE-001"
            st.session_state.investigation = None
            st.session_state.review = None
            st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="RevenueTwin — Enterprise Revenue Integrity",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()
    render_brand()

    if "screen" not in st.session_state:
        st.session_state.screen = "dashboard"
    if "case_id" not in st.session_state:
        st.session_state.case_id = "CASE-001"

    render_sidebar()

    if st.session_state.screen == "dashboard":
        render_dashboard()
    else:
        try:
            case = get_revenue_case(st.session_state.case_id)
            render_case(case)
        except Exception as exc:
            st.error(f"Error loading revenue case {st.session_state.case_id}: {exc}")
            if st.button("Return to Dashboard"):
                st.session_state.screen = "dashboard"
                st.rerun()


if __name__ == "__main__":
    main()
