from app.schemas import PromptRequest, PromptResponse
from app.core.graph import Graph

config = {"configurable": {"thread_id": "1"}}

graph = Graph()

def ask(prompt: PromptRequest) -> PromptResponse:
    res = None
    for event in graph.get_graph().stream(
        {"messages": [{"role": "user", "content": prompt.message}]},
        config=config,
        stream_mode="values"
    ):
        res = event["messages"][-1]
    if "Ask user" in res.content:
        res.content = res.content.replace("Ask user:", "")
    return PromptResponse(message=res.content if res else "No response")

def change_model(model_name):
    graph.set_model(model_name)
    return "success"

def clear_memory():
    graph.clear_memory()
    return "success"