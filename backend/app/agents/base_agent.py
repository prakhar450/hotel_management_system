from __future__ import annotations
import time
import uuid
from typing import Any, Optional

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.agent_log import AgentLog

MAX_TOKENS = 1000
TEMPERATURE = 0.3
TIMEOUT_SECONDS = 10
MODEL = "claude-sonnet-4-20250514"

# Human-readable labels shown in the team chat UI
AGENT_LABELS = {
    "front_desk": "🛎️  Front Desk",
    "accounting": "📊  Accounting",
    "inventory": "📦  Inventory",
    "sales": "🤝  Sales",
    "manager": "👔  General Manager",
    "system": "⚙️  System",
}


class BaseAgent:
    """
    All agents inherit from this. Handles the Anthropic tool-use loop,
    logs every step to agent_logs so the team-chat view has full history.
    """

    name: str = "base"
    system_prompt: str = ""
    tools: list[dict] = []

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def invoke(
        self,
        task: str,
        context: dict,
        db: Session,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> str:
        """
        Run the agent. Returns the final text response.
        All intermediate steps are logged as separate agent_log rows.
        """
        if conversation_id is None:
            conversation_id = uuid.uuid4()

        self._log_step(
            db, conversation_id, step_order=0,
            message_type="user_request",
            action=f"Task assigned to {self.name}",
            input_data={"task": task, "context": context},
            output_data={},
            sender_label="⚡ Orchestrator",
        )

        start = time.time()
        result_text = ""
        success = True
        error_msg = None

        try:
            result_text = self._run(task, context, db, conversation_id)
        except anthropic.APITimeoutError:
            success = False
            error_msg = "Agent timed out"
            result_text = "I'm taking too long to respond — please handle this manually."
        except anthropic.APIError as e:
            success = False
            error_msg = f"Claude API error: {str(e)}"
            result_text = "I hit a technical issue — please handle this manually."
        except Exception as e:
            success = False
            error_msg = str(e)
            result_text = "Something went wrong — please handle this manually."

        duration_ms = int((time.time() - start) * 1000)

        self._log_step(
            db, conversation_id, step_order=99,
            message_type="response",
            action=f"{self.name} final response",
            input_data={"task": task},
            output_data={"response": result_text},
            sender_label=AGENT_LABELS.get(self.name, self.name),
            success=success,
            error_message=error_msg,
            duration_ms=duration_ms,
        )

        return result_text

    def _run(self, task: str, context: dict, db: Session, conversation_id: uuid.UUID) -> str:
        """Agentic tool-use loop."""
        messages = [{"role": "user", "content": self._build_user_message(task, context)}]
        step = 1

        for _ in range(5):
            kwargs: dict[str, Any] = {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "system": self.system_prompt,
                "messages": messages,
                "timeout": TIMEOUT_SECONDS,
            }
            if self.tools:
                kwargs["tools"] = self.tools

            response = self.client.messages.create(**kwargs)

            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        # Log the tool call
                        self._log_step(
                            db, conversation_id, step_order=step,
                            message_type="tool_call",
                            action=f"Calling tool: {block.name}",
                            input_data=block.input,
                            output_data={},
                            sender_label=AGENT_LABELS.get(self.name, self.name),
                        )
                        step += 1

                        result = self._execute_tool(block.name, block.input, db)

                        # Log the tool result
                        self._log_step(
                            db, conversation_id, step_order=step,
                            message_type="tool_result",
                            action=f"Result from: {block.name}",
                            input_data={"tool": block.name},
                            output_data={"result": result},
                            sender_label="⚙️  System",
                        )
                        step += 1

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            return self._extract_text(response)

        return "Agent reached maximum reasoning steps — please handle manually."

    def _execute_tool(self, tool_name: str, tool_input: dict, db: Session) -> Any:
        return f"Tool '{tool_name}' not implemented in {self.name}"

    def _build_user_message(self, task: str, context: dict) -> str:
        ctx_str = "\n".join(f"  {k}: {v}" for k, v in context.items())
        return f"Task: {task}\n\nContext:\n{ctx_str}" if ctx_str else f"Task: {task}"

    def _extract_text(self, response) -> str:
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def _log_step(
        self,
        db: Session,
        conversation_id: uuid.UUID,
        step_order: int,
        message_type: str,
        action: str,
        input_data: dict,
        output_data: dict,
        sender_label: str,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        try:
            log = AgentLog(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                agent_name=self.name,
                message_type=message_type,
                step_order=step_order,
                sender_label=sender_label,
                action=action[:200],
                input_data=input_data,
                output_data=output_data,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            db.add(log)
            db.commit()
        except Exception:
            pass  # logging must never crash the main flow
