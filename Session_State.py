# TODO Phase 1: shared state, agent order, agent-selection logic

from operator import add
from typing import Annotated, TypedDict

from graph_nodes.slides_agent import Slide
from graph_nodes.code_agent import CodeExample
from graph_nodes.quiz_agent import QuizQuestion

from typing_extensions import Literal

class SessionBrief(TypedDict):
    session_id: str
    lecturer_id: str
    topic: str
    course_name: str
    student_level: str
    duration_minutes: int
    language: str
    programming_language: str
    needs: list[str]
    num_quiz_questions: int
    learning_objectives: list[str]
    notes: str

class SessionState(TypedDict):
    # 1) Input 
    brief: SessionBrief

    # 2) Orchestrator 
    selected_agents: list[str]
    reasoning: str
    memory_context: list[str]

    # 3) Agents 
    outline: list[str]
    slides: list[Slide]
    code_examples: list[CodeExample]
    quiz: list[QuizQuestion]

    # 4) Draft + revision
    draft: dict
    approval_status: Literal["pending", "approved", "revise"]
    feedback: str
    revision_count: int

    # 5) final output
    final_output: dict
    messages: Annotated[list[str], add]


AgentName = Literal["research_agent", "slides_agent", "code_agent", "quiz_agent"]
AGENT_ORDER: list[AgentName] = ["research_agent", "slides_agent", "code_agent", "quiz_agent"]

def next_agent(state, current) -> str:

    selected = state["selected_agents"]

    if current in AGENT_ORDER:
        current_index=AGENT_ORDER.index(current)
        if current_index + 1 < len(AGENT_ORDER):
            next_agent = AGENT_ORDER[current_index + 1]
            if next_agent in selected:
                return next_agent
    elif current not in AGENT_ORDER:
        next_agent = AGENT_ORDER[0]
    else:
        return "draft_agent"