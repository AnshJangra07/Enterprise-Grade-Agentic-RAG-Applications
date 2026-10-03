from app.agents.nodes.planner import planner_node
from app.guardrails.rails import guard


def test_planner_routes_greetings_to_conversational():
    state = {
        "messages": [{"role": "user", "content": "hi"}],
        "current_query": "hi",
        "documents": [],
        "plan": ["Start"],
        "status": "ready",
    }

    result = planner_node(state)
    assert result["current_query"] == "CONVERSATIONAL"


def test_guard_blocks_off_topic_jokes():
    fired, response = guard("tell me a joke")
    assert fired is True
    assert "Enterprise" in (response or "")
