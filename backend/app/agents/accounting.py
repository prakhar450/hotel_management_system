from __future__ import annotations
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.models.invoice import Invoice
from app.models.payment import Payment

ESCALATE_DISCREPANCY_INR = 500
ESCALATE_OVERDUE_DAYS = 7


class AccountingAgent(BaseAgent):
    name = "accounting"
    system_prompt = """You are the Accounting Agent for a hotel and wedding venue in India.
Your job: answer questions about invoices, payments, and revenue. Flag discrepancies and overdue invoices.

Tone: precise and formal — like a careful accountant.

Rules:
- You NEVER modify prices, apply discounts, or issue refunds. You only read and report.
- If a payment discrepancy exceeds ₹500 or an invoice is overdue by more than 7 days, respond with ESCALATE: <reason>.
- Always quote amounts in Indian Rupees (₹).
- Summarise numbers clearly — total due, total paid, balance remaining."""

    tools = [
        {
            "name": "get_invoice",
            "description": "Fetch invoice details by invoice number or ID",
            "input_schema": {
                "type": "object",
                "properties": {"invoice_number": {"type": "string"}},
                "required": ["invoice_number"],
            },
        },
        {
            "name": "get_payments_for_invoice",
            "description": "List all payments recorded against an invoice",
            "input_schema": {
                "type": "object",
                "properties": {"invoice_id": {"type": "string"}},
                "required": ["invoice_id"],
            },
        },
        {
            "name": "list_overdue_invoices",
            "description": "Get all invoices that are overdue today",
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
    ]

    def _execute_tool(self, tool_name: str, tool_input: dict, db: Session) -> Any:
        if tool_name == "get_invoice":
            invoice = db.query(Invoice).filter(
                Invoice.invoice_number == tool_input["invoice_number"]
            ).first()
            if not invoice:
                return "Invoice not found"
            paid = sum(float(p.amount) for p in invoice.payments)
            return {
                "invoice_number": invoice.invoice_number,
                "total_amount": float(invoice.total_amount),
                "paid": paid,
                "balance": float(invoice.total_amount) - paid,
                "status": invoice.status,
                "due_date": str(invoice.due_date),
                "line_items": invoice.line_items,
            }

        if tool_name == "get_payments_for_invoice":
            import uuid as _uuid
            payments = db.query(Payment).filter(
                Payment.invoice_id == _uuid.UUID(tool_input["invoice_id"])
            ).all()
            return [
                {"amount": float(p.amount), "method": p.method,
                 "date": str(p.payment_date), "ref": p.reference_number}
                for p in payments
            ]

        if tool_name == "list_overdue_invoices":
            overdue = db.query(Invoice).filter(
                Invoice.due_date < date.today(),
                Invoice.status.in_(["sent", "overdue"]),
            ).all()
            return [
                {"invoice_number": inv.invoice_number,
                 "total": float(inv.total_amount),
                 "due_date": str(inv.due_date),
                 "days_overdue": (date.today() - inv.due_date).days}
                for inv in overdue
            ]

        return f"Unknown tool: {tool_name}"
