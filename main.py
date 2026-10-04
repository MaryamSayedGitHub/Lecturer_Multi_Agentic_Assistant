# TODO Phase 11: FastAPI entrypoint
from llm.llm_provider import choose_provider, get_llm

if __name__ == "__main__":
    choose_provider(ask=True)   # بتسأل مرة واحدة هنا بس
    # uvicorn.run(...)


llm = get_llm()                                   # الاختيار العام
llm = get_llm(provider="gemini", temperature=0.4) # override لـ agent معين