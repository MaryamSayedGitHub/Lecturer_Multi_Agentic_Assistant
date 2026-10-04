"""
Phase 2 checkpoint.

Run:
    uv run python test_llm.py              # every provider configured in .env
    uv run python test_llm.py groq         # one provider
    uv run python test_llm.py groq gemini  # two providers

Steps:
  0) Check that every prompt builds and has the expected variables (no LLM call)
  1) Plain text
  2) Simple structured output
  3) QUIZ_PROMPT | llm.with_structured_output(QuizOutput)
"""

import sys

from pydantic import BaseModel, Field

import prompts
from llm.llm_provider import PROVIDERS, _missing, get_llm
from schemas import QuizOutput


class Capital(BaseModel):
    country: str
    capital: str = Field(description="Capital city name")


def check_prompts() -> None:
    print("== Step 0: prompt variables ==")
    for name in ["ORCHESTRATOR_PROMPT", "RESEARCH_PROMPT", "SLIDES_PROMPT", "CODE_PROMPT", "QUIZ_PROMPT"]:
        p = getattr(prompts, name)
        print(f"{name:20} -> {sorted(p.input_variables)}")
    print()


def test_provider(provider: str) -> None:
    print(f"== {provider} ==")
    llm = get_llm(provider=provider)

    # 1) text
    print("1) text:", llm.invoke("Say hi in one short sentence.").content)

    # 2) simple structured output
    print("2) structured:", llm.with_structured_output(Capital).invoke("What is the capital of Egypt?"))

    # 3) quiz chain
    chain = prompts.QUIZ_PROMPT | llm.with_structured_output(QuizOutput)
    result = chain.invoke({
        "topic": "Python decorators",
        "outline": "- Functions are objects\n- Closures\n- Writing a decorator",
        "level": "intermediate",
        "num_questions": 3,
        "language": "English",
        "feedback": "None",
    })

    assert len(result.questions) == 3, f"expected 3 questions, got {len(result.questions)}"
    for i, q in enumerate(result.questions, 1):
        print(f"   Q{i}: {q.question}")
        for j, opt in enumerate(q.options):
            print(f"      {'*' if j == q.answer_index else ' '} {opt}")
    print("3) quiz: OK\n")


if __name__ == "__main__":
    check_prompts()

    requested = sys.argv[1:] or [p for p in PROVIDERS if not _missing(p)]
    if not requested:
        sys.exit("No provider is configured. Fill the key and model name in .env.")

    for provider in requested:
        try:
            test_provider(provider)
        except Exception as e:  # keep going with the other providers if one fails
            print(f"[{provider}] FAILED: {type(e).__name__}: {e}\n")