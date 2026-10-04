# TODO Phase 5: build + compile the LangGraph graph
from Session_State import next_agent
import graph


def route_after(current):
    def router(state):
        return next_agent(state, current)
    return router

graph.add_conditional_edges("orchestrator", route_after("orchestrator"))
graph.add_conditional_edges("research_agent", route_after("research_agent"))
graph.add_conditional_edges("slides_agent", route_after("slides_agent"))
graph.add_conditional_edges("code_agent", route_after("code_agent"))
graph.add_conditional_edges("quiz_agent", route_after("quiz_agent"))