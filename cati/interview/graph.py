"""LangGraph StateGraph — the interview brain.

Node routing:
  START → greet → ask_question → listen_and_parse
                                       ↓
                              handle_refusal / handle_unclear / ask_question / close_interview
                                                                                    ↓
                                                                                  END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from cati.interview.nodes import (
    ask_question,
    close_interview,
    greet,
    handle_refusal,
    handle_unclear,
    listen_and_parse,
)
from cati.interview.state import InterviewState


def _route(state: InterviewState) -> str:
    """Conditional edge: read state.next_node to determine routing."""
    return state.next_node or END


def build_interview_graph():
    """Build and compile the CATI interview LangGraph."""
    graph = StateGraph(InterviewState)

    # Add nodes
    graph.add_node("greet", greet)
    graph.add_node("ask_question", ask_question)
    graph.add_node("listen_and_parse", listen_and_parse)
    graph.add_node("handle_refusal", handle_refusal)
    graph.add_node("handle_unclear", handle_unclear)
    graph.add_node("close_interview", close_interview)

    # Entry
    graph.add_edge(START, "greet")

    # Conditional routing from each node via next_node field
    for node in ("greet", "ask_question", "listen_and_parse", "handle_refusal", "handle_unclear"):
        graph.add_conditional_edges(
            node,
            _route,
            {
                "ask_question": "ask_question",
                "listen_and_parse": "listen_and_parse",
                "handle_refusal": "handle_refusal",
                "handle_unclear": "handle_unclear",
                "close_interview": "close_interview",
                END: END,
            },
        )

    graph.add_edge("close_interview", END)

    return graph.compile()


# Singleton compiled graph
_graph = None


def get_interview_graph():
    global _graph
    if _graph is None:
        _graph = build_interview_graph()
    return _graph
