"""
Pydantic models = the shape of the output we ask the LLM to produce.

Why Pydantic and not TypedDict?
- with_structured_output(Model) sends the schema (field names + descriptions) to the model.
- After the reply, Pydantic validates it. If the model returns something wrong, an error is
  raised here instead of the bad data flowing on through the graph.

Every Field(description=...) is sent to the model, so write it as if you were explaining
to the model what the field should contain.

Note: RoutingDecision (the orchestrator's decision) is created in Phase 4 inside
graph_nodes/orchestrator.py. It needs AgentName from Session_State.py, and putting it here
would cause a circular import.
"""

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------- research
class OutlineOutput(BaseModel):
    sections: list[str] = Field(
        description="Ordered section titles of the session, from the first to the last."
    )


# ------------------------------------------------------------------ slides
class Slide(BaseModel):
    title: str = Field(description="Short slide title.")
    bullets: list[str] = Field(
        description="3 to 5 short bullet points. Each bullet is at most 12 words."
    )
    notes: str = Field(
        description="Speaker notes: 2 to 4 sentences the lecturer can say while showing this slide."
    )


class SlidesOutput(BaseModel):
    slides: list[Slide]


# -------------------------------------------------------------------- code
class CodeExample(BaseModel):
    title: str = Field(description="What this example demonstrates.")
    code: str = Field(
        description="Complete, runnable code. Self-contained: no input(), no files, no network."
    )
    explanation: str = Field(
        description="Step-by-step explanation of what the code does and what it prints."
    )


class CodeOutput(BaseModel):
    examples: list[CodeExample]


# -------------------------------------------------------------------- quiz
class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(description="Exactly 4 answer options.")
    answer_index: int = Field(description="0-based index of the single correct option.")
    explanation: str = Field(description="1 to 2 sentences explaining why the answer is correct.")

    @field_validator("options")
    @classmethod
    def must_have_four_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError("options must contain exactly 4 items")
        return v

    @model_validator(mode="after")
    def answer_in_range(self):
        if not 0 <= self.answer_index < len(self.options):
            raise ValueError("answer_index must point to one of the options")
        return self


class QuizOutput(BaseModel):
    # Wrapper around the list: some providers do not accept a list as the schema root.
    questions: list[QuizQuestion]