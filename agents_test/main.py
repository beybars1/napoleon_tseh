"""
Simple Multi-Agent System: Math Question Generator & Solver
Run: python math_agents.py
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Define the shared state between agents
class MathAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    question: str
    solution: str
    current_agent: str

# Agent 1: Question Generator
def question_generator(state: MathAgentState):
    """Generate a random math question"""
    print("\n🎲 Question Generator Agent is working...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)
    
    prompt = """Generate ONE random math problem. Make it interesting but solvable.
    Include problems like: algebra, geometry, word problems, calculus, etc.
    Just provide the question, nothing else."""
    
    response = llm.invoke(prompt)
    question = response.content
    
    print(f"📝 Generated Question: {question}")
    
    return {
        "question": question,
        "current_agent": "generator",
        "messages": [{"role": "assistant", "content": f"Question: {question}"}]
    }

# Agent 2: Problem Solver
def problem_solver(state: MathAgentState):
    """Solve the math question"""
    print("\n🧮 Problem Solver Agent is working...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = f"""Solve this math problem step by step:

{state['question']}

Provide:
1. Clear step-by-step solution
2. Final answer

Be thorough but concise."""
    
    response = llm.invoke(prompt)
    solution = response.content
    
    print(f"✅ Solution:\n{solution}")
    
    return {
        "solution": solution,
        "current_agent": "solver",
        "messages": [{"role": "assistant", "content": f"Solution: {solution}"}]
    }

# Router function - decides which agent runs next
def router(state: MathAgentState):
    """Route to appropriate agent based on current state"""
    if not state.get("question"):
        # No question yet, go to generator
        return "generator"
    elif not state.get("solution"):
        # Question exists but no solution, go to solver
        return "solver"
    else:
        # Both exist, we're done
        return "end"

# Build the graph
def create_math_agent_graph():
    """Create and compile the multi-agent graph"""
    
    # Initialize the graph with our state
    workflow = StateGraph(MathAgentState)
    
    # Add nodes (agents)
    workflow.add_node("generator", question_generator)
    workflow.add_node("solver", problem_solver)
    
    # Set entry point - start with routing
    workflow.set_entry_point("router")
    
    # Add a router node that decides what to do
    def route_node(state: MathAgentState):
        """Routing node - doesn't modify state"""
        return state
    
    workflow.add_node("router", route_node)
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        router,  # Function that returns next node name
        {
            "generator": "generator",
            "solver": "solver",
            "end": END
        }
    )
    
    # After generator, go back to router
    workflow.add_edge("generator", "router")
    
    # After solver, go to end
    workflow.add_edge("solver", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app

# Main execution
def main():
    print("=" * 60)
    print("🤖 Multi-Agent Math System Starting...")
    print("=" * 60)
    
    # Create the graph
    app = create_math_agent_graph()
    
    # Initial state
    initial_state = {
        "messages": [],
        "question": "",
        "solution": "",
        "current_agent": ""
    }
    
    # Run the graph
    print("\n▶️  Running multi-agent workflow...\n")
    final_state = app.invoke(initial_state)
    
    # Display results
    print("\n" + "=" * 60)
    print("✨ FINAL RESULTS")
    print("=" * 60)
    print(f"\n📌 Question:\n{final_state['question']}")
    print(f"\n📌 Solution:\n{final_state['solution']}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()