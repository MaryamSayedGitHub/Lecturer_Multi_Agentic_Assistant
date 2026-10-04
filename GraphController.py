# TODO Phase 11: class that wraps graph (run / resume / get state)


class GraphController:
    def __init__(self, graph):
        self.graph = graph

    def run(self, state):
        return self.graph.run(state)

    def resume(self, state):
        return self.graph.resume(state)

    def get_state(self, state):
        return self.graph.get_state(state)