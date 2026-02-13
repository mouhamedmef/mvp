from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class ChatState(TypedDict):
    user_input: str
    bot_output: str


def echo_node(state: ChatState) -> ChatState:
    return {
        "user_input": state["user_input"],
        "bot_output": state["user_input"],
    }


builder = StateGraph(ChatState)
builder.add_node("echo", echo_node)
builder.add_edge(START, "echo")
builder.add_edge("echo", END)

graph = builder.compile()
