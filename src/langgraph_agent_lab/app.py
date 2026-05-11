import streamlit as st
import os
import sqlite3

# Enable real interrupt for HITL
os.environ["LANGGRAPH_INTERRUPT"] = "true"

from langgraph_agent_lab.graph import build_graph
from langgraph_agent_lab.persistence import build_checkpointer
from langgraph_agent_lab.state import Scenario, initial_state

st.set_page_config(page_title="LangGraph Support Agent", layout="wide")
st.title("LangGraph Support Agent - Lab 23")

@st.cache_resource
def init_system():
    checkpointer = build_checkpointer(kind="sqlite", database_url="streamlit_app.db")
    graph = build_graph(checkpointer=checkpointer)
    return graph

graph = init_system()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "thread-ui-1"

st.sidebar.header("Agent Controls")
query = st.sidebar.text_input("Enter your request:", "I need a refund for my order.")
thread_id = st.sidebar.text_input("Thread ID (for Time Travel/Recovery):", st.session_state.thread_id)
st.session_state.thread_id = thread_id

config = {"configurable": {"thread_id": st.session_state.thread_id}}

if st.sidebar.button("Submit Request"):
    scenario = Scenario(id="UI_01", query=query, expected_route="simple")
    state = initial_state(scenario)
    state["thread_id"] = st.session_state.thread_id
    
    st.write("### Execution Trace")
    # Execute graph
    for event in graph.stream(state, config=config, stream_mode="values"):
        pass
    st.success("Execution reached next state.")

# Check current state for interrupts
current_state = graph.get_state(config)

st.write("---")
st.write("### Current Agent State")
if current_state and current_state.values:
    with st.expander("View Raw State JSON"):
        st.json(current_state.values)
    
    # If there's no next node, the graph has finished executing
    if not current_state.next:
        st.success("✅ **Quy trình đã hoàn tất!**")
        
        # Display the final answer or clarification question
        if current_state.values.get("final_answer"):
            st.info(f"**🤖 Agent:** {current_state.values.get('final_answer')}")
        elif current_state.values.get("pending_question"):
            st.warning(f"**🤖 Agent (Cần thêm thông tin):** {current_state.values.get('pending_question')}")
else:
    st.info("No active state for this thread.")

if current_state and current_state.next:
    st.warning("⚠️ **Human-in-the-Loop Required!** The graph has paused for approval.")
    
    # Check if we are paused at the approval node
    if "approval" in current_state.next:
        st.write("Review the proposed action and approve or reject.")
        approved = st.checkbox("Approve Action?", value=True)
        comment = st.text_input("Reviewer Comment", "Approved via Streamlit UI")
        
        if st.button("Submit Decision"):
            from langgraph.types import Command
            
            # Resume graph with interrupt response
            # Command(resume=...) is used in newer LangGraph for interrupt()
            resume_val = {"approved": approved, "comment": comment}
            try:
                for event in graph.stream(Command(resume=resume_val), config=config, stream_mode="values"):
                    pass
                import time
                if approved:
                    st.success("Đã chấp nhận thành công!")
                else:
                    st.warning("Đã từ chối yêu cầu!")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error resuming graph: {e}")

st.write("---")
st.write("### Time Travel (Checkpoint History)")
if st.button("Load History"):
    history = list(graph.get_state_history(config))
    if not history:
        st.info("No history found for this thread.")
    else:
        for idx, h in enumerate(history):
            with st.expander(f"Step {len(history) - idx} - Checkpoint: {h.config['configurable']['checkpoint_id']}"):
                st.json(h.values)
