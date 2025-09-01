from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import os
from langchain.chat_models import init_chat_model
from .tools import *
from langgraph.checkpoint.memory import InMemorySaver
import json
from langchain_core.messages import ToolMessage, HumanMessage
from .config import API_KEY, ANTHROPIC_API_KEY
from langchain_core.messages import SystemMessage
os.environ["GOOGLE_API_KEY"] = API_KEY

class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        print("Tool Node Input:", inputs)
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}
    
class State(TypedDict):
    messages: Annotated[list, add_messages]


class Graph():
    def __init__(self):
        self.config = {"configurable": {"thread_id": "1"}}
        self.memory = InMemorySaver()
        self.graph_builder = StateGraph(State)

        self.llm = init_chat_model("google_genai:gemini-2.0-flash")
        self.supervisor_llm = init_chat_model("google_genai:gemini-2.0-flash")

        self.llm_with_tools = self.llm.bind_tools(tools)
        self.tool_node = BasicToolNode(tools=tools)
        self.graph_builder.add_node("agent", self.agent)
        self.graph_builder.add_node("supervisor", self.supervisor)
        self.graph_builder.add_node("tools", self.tool_node)

        self.graph_builder.add_edge(START, "supervisor")
        self.state_ = self.graph_builder.add_conditional_edges(
            "supervisor",
            lambda state: 
            "agent" if 
                state["messages"][-1].content and ("Project is done" not in state["messages"][-1].content and "Ask user:" not in state["messages"][-1].content)
                else END,
            {"agent": "agent", END: END}
        )
            
        self.graph_builder.add_conditional_edges(
            "agent",
            lambda state: (
                "tools"
                if state.get("messages") 
                and hasattr(state["messages"][-1], "tool_calls") 
                and state["messages"][-1].tool_calls
                else "supervisor"
            ),
            {"tools": "tools", "supervisor": "supervisor"}
        )
        self.graph_builder.add_edge("tools", "agent")
        self.graph = self.graph_builder.compile(checkpointer=self.memory)

    def clear_memory(self):
        self.memory = InMemorySaver()
        self.graph = self.graph_builder.compile(checkpointer=self.memory)
    def get_graph(self):
        return self.graph
    
    def set_model(self, model_name):
        self.llm = init_chat_model(model_name)
        self.supervisor_llm = init_chat_model(model_name)
        self.llm_with_tools = self.llm.bind_tools(tools)

    def agent(self,state: State):
        messages = state["messages"]
        return {"messages": [self.llm_with_tools.invoke(messages)]}
    
    def supervisor(self,state: State):
        """
        Supervisor reads all messages and guides the agent.
        Can ask questions, request tool execution, or discuss with the agent autonomously.
        Acts as a virtual user.
        """
        messages = state["messages"]
        
        # Supervisor system prompt in English
        system_prompt = (
            "You are a virtual User. Your task is to guide the agent in performing tasks to build the whole project. "
            "You just need to tell the agent what file or folder to create and what content to write in each file. "
            "Play like a real user. When the project is done, say 'Project is done'."
            "You will recevie request from system(real user) and create following the request."
            "if the init request is not clear or just want to chat with real user, must ask for more details by using this pattern: Ask user: ...your question..."
        )


        # Flatten conversation history safely
        conversation_history = []
        for m in messages:
            if not hasattr(m, "content"):
                continue

            # Xác định role
            role = getattr(m, "type", "unknown")
            if hasattr(m, "additional_kwargs"):
                role = m.additional_kwargs.get("role", role)

            # Xử lý content (list hoặc string)
            if isinstance(m.content, list):
                content = "\n".join(map(str, m.content))
            else:
                content = str(m.content)

            conversation_history.append(f"[{role}] {content}")

        # Construct a HumanMessage as if user sent it
        supervisor_message = HumanMessage(
            content=system_prompt + "\n\nCurrent conversation:\n" + "\n".join(conversation_history)
        )

        # Call the LLM to produce instructions for the agent
        llm_output = self.supervisor_llm.invoke([supervisor_message])

        # Wrap output as HumanMessage so agent sees it as a user instruction
        output = HumanMessage(content=llm_output.content)
        return {"messages": [output]}