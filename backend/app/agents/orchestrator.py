from __future__ import annotations
import uuid

from sqlalchemy.orm import Session

from app.agents.front_desk import FrontDeskAgent
from app.agents.accounting import AccountingAgent
from app.agents.inventory import InventoryAgent
from app.agents.sales import SalesAgent
from app.agents.manager import ManagerAgent

_AGENTS = {
    "front_desk": FrontDeskAgent,
    "accounting": AccountingAgent,
    "inventory": InventoryAgent,
    "sales": SalesAgent,
    "manager": ManagerAgent,
}


def invoke_agent(agent_name: str, task: str, context: dict, db: Session) -> dict:
    """
    Route a task to the right agent. All messages share a conversation_id
    so the chat view can thread them together. Escalations continue in the
    same conversation — the manager's reply appears in the same thread.
    """
    conversation_id = uuid.uuid4()

    AgentClass = _AGENTS.get(agent_name)
    if not AgentClass:
        return {
            "agent_name": agent_name,
            "response": f"Unknown agent '{agent_name}'. Valid: {list(_AGENTS.keys())}",
            "escalated": False,
            "conversation_id": str(conversation_id),
        }

    agent = AgentClass()
    response = agent.invoke(task, context, db, conversation_id=conversation_id)

    if response.strip().startswith("ESCALATE:"):
        reason = response.replace("ESCALATE:", "").strip()
        escalation_task = (
            f"Escalation from {agent_name.replace('_', ' ').title()}: {reason}\n\n"
            f"Original task: {task}"
        )
        manager = ManagerAgent()
        manager_response = manager.invoke(
            escalation_task, context, db, conversation_id=conversation_id
        )
        return {
            "agent_name": "manager",
            "response": manager_response,
            "escalated": True,
            "escalated_from": agent_name,
            "escalation_reason": reason,
            "conversation_id": str(conversation_id),
        }

    return {
        "agent_name": agent_name,
        "response": response,
        "escalated": False,
        "conversation_id": str(conversation_id),
    }
