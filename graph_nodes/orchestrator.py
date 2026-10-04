from pydantic import BaseModel, Field

from graph_nodes.utils import format_optional
from graph_nodes.utils import build_chain, format_optional
from prompts import ORCHESTRATOR_PROMPT
from Session_State import AGENT_ORDER, AgentName

# Maps what the lecturer ticks in the form ("needs") to an agent name.
NEEDS_TO_AGENT = {
    "slides": "slides_agent",
    "code": "code_agent",
    "quiz": "quiz_agent",
}


class RoutingDecision(BaseModel):
    selected_agents: list[AgentName] = Field(
        description="The specialist agents that must run. Always includes research_agent."
    )
    reasoning: str = Field(
        description="1 or 2 short sentences for the lecturer explaining why these agents were chosen."
    )


def rule_based_agents(needs: list[str]) -> list[str]:
    """The simple version: no LLM, just map the checkboxes to agents."""
    wanted = {NEEDS_TO_AGENT[n] for n in needs if n in NEEDS_TO_AGENT}
    return [a for a in AGENT_ORDER if a == "research_agent" or a in wanted]


def normalize(agents: list[str]) -> list[str]:
    """Safety net: research_agent is always there, no duplicates, fixed order."""
    return [a for a in AGENT_ORDER if a == "research_agent" or a in agents]


def orchestrator(state) -> dict:
    """Reads: brief, memory_context, feedback.   Writes: selected_agents, reasoning."""
    brief = state["brief"]

    chain = build_chain(ORCHESTRATOR_PROMPT, RoutingDecision, temperature=0)

    try:
        result = chain.invoke({
            "topic": brief["topic"],
            "needs": ", ".join(brief["needs"]),
            "notes": format_optional(brief.get("notes")),
            "memory_context": format_optional(state.get("memory_context")),
            "feedback": format_optional(state.get("feedback")),
            "language": brief["language"],
        })
        selected = normalize(result.selected_agents)
        reasoning = result.reasoning
    except Exception as e:
        # Print the real reason, otherwise a wrong API key looks the same as a bad JSON.
        print(f"[orchestrator] LLM decision failed, using rules. {type(e).__name__}: {str(e)[:300]}")
        selected = rule_based_agents(brief["needs"])
        reasoning = "Plan built from the requested outputs."

    return {
        "selected_agents": selected,
        "reasoning": reasoning,
        "messages": [f"orchestrator: {', '.join(selected)}"],
    }