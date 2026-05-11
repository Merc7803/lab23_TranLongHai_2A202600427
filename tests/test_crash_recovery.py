import sqlite3
import os
import pytest
from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.persistence import build_checkpointer
from langgraph_agent_lab.state import Scenario, initial_state

def test_crash_recovery(tmp_path):
    """Demonstrate that SQLite checkpoint survives process kill + restart."""
    
    db_path = tmp_path / "test_checkpoints.db"
    
    # Process 1: Initialize, run partway, then "crash"
    # We will simulate a "crash" by pausing at an interrupt
    os.environ["LANGGRAPH_INTERRUPT"] = "true"
    
    checkpointer1 = build_checkpointer(kind="sqlite", database_url=str(db_path))
    graph1 = build_graph(checkpointer=checkpointer1)
    
    thread_id = "test-crash-thread"
    config = {"configurable": {"thread_id": thread_id}}
    
    scenario = Scenario(id="CRASH_01", query="Refund the user immediately", expected_route="risky")
    state = initial_state(scenario)
    state["thread_id"] = thread_id
    
    # Run graph1. It should pause at approval
    for event in graph1.stream(state, config=config, stream_mode="values"):
        pass
        
    current_state1 = graph1.get_state(config)
    assert current_state1.next == ("approval",)
    
    # Simulate CRASH: Destroy graph1 and checkpointer1
    del graph1
    del checkpointer1
    
    # Process 2: Restart and recover
    checkpointer2 = build_checkpointer(kind="sqlite", database_url=str(db_path))
    graph2 = build_graph(checkpointer=checkpointer2)
    
    # Fetch state for the same thread
    current_state2 = graph2.get_state(config)
    
    # Validate we recovered the state exactly where we left off
    assert current_state2 is not None
    assert current_state2.next == ("approval",)
    assert current_state2.values["route"] == "risky"
    assert current_state2.values["risk_level"] == "high"
    
    print("Crash recovery successful: State reloaded from SQLite checkpoint.")
