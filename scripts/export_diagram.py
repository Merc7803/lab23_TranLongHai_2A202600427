import os
from langgraph_agent_lab.graph import build_graph

def export_diagram():
    print("Building graph...")
    graph = build_graph()
    
    diagram_path = os.path.join(os.path.dirname(__file__), "..", "reports", "graph_diagram.png")
    os.makedirs(os.path.dirname(diagram_path), exist_ok=True)
    
    print(f"Exporting diagram to {diagram_path}...")
    try:
        # Generate raw image bytes
        image_bytes = graph.get_graph().draw_mermaid_png()
        with open(diagram_path, "wb") as f:
            f.write(image_bytes)
        print("Success!")
    except Exception as e:
        print(f"Failed to export diagram: {e}")
        print("Mermaid diagram code:")
        print(graph.get_graph().draw_mermaid())

if __name__ == "__main__":
    export_diagram()
