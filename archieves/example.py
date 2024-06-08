!pip install openai httpx python-dotenv langchain

from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ChatMessage

import httpx
import os

# Initialize in-memory SQLite
memory = SqliteSaver.from_conn_string(":memory:")

# Define the agent state
class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int

# Define the prompts
PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. 
Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes 
or instructions for the sections."""

WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.
Generate the best essay possible for the user's request and the initial outline. 
If the user provides critique, respond with a revised version of your previous attempts. 
Utilize all the information below as needed: 

------

{content}"""

REFLECTION_PROMPT = """You are a teacher grading an essay submission. 
Generate critique and recommendations for the user's submission. 
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can 
be used when writing the following essay. Generate a list of search queries that will gather 
any relevant information. Only generate 3 queries max."""

RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can 
be used when making any requested revisions (as outlined below). 
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""

# Set the base URL for the local LLM server
llama3_base_url = "http://192.168.86.51:8081/v1/chat/completions"

def generate_response(messages):
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "messages": messages,
        "max_gen_len": 150,
        "temperature": 0.1,
        "top_p": 0.9,
        "do_sample": True
    }

    try:
        response = httpx.post(llama3_base_url, headers=headers, json=payload, timeout=60.0)  # Increased timeout
        response.raise_for_status()
    except httpx.TimeoutException:
        raise Exception("Request timed out")
    except httpx.RequestError as e:
        raise Exception(f"An error occurred while requesting {e.request.url!r}.")
    
    result = response.json()
    return result['choices'][0]['message']['content']

def plan_node(state: AgentState):
    response = generate_response([
        {"role": "system", "content": PLAN_PROMPT},
        {"role": "user", "content": state['task']}
    ])
    return {"plan": response}

def generation_node(state: AgentState):
    response = generate_response([
        {"role": "system", "content": WRITER_PROMPT.format(content=state['content'])},
        {"role": "user", "content": state['plan']}
    ])
    return {"draft": response}

def reflection_node(state: AgentState):
    response = generate_response([
        {"role": "system", "content": REFLECTION_PROMPT},
        {"role": "user", "content": state['draft']}
    ])
    return {"critique": response}

def research_plan_node(state: AgentState):
    queries = generate_response([
        {"role": "system", "content": RESEARCH_PLAN_PROMPT},
        {"role": "user", "content": state['plan']}
    ])
    return {"content": queries.split('\n')}

def research_critique_node(state: AgentState):
    queries = generate_response([
        {"role": "system", "content": RESEARCH_CRITIQUE_PROMPT},
        {"role": "user", "content": state['critique']}
    ])
    content = state['content'] or []
    
    content.extend(queries.split('\n'))
    return {"content": content}

def should_continue(state):
    state["revision_number"] += 1  # Increment revision number
    if state["revision_number"] >= state["max_revisions"]:
        return END
    return "reflect"

builder = StateGraph(AgentState)

builder.add_node("planner", plan_node)
builder.add_node("generate", generation_node)
builder.add_node("reflect", reflection_node)
builder.add_node("research_plan", research_plan_node)
builder.add_node("research_critique", research_critique_node)

builder.set_entry_point("planner")

builder.add_conditional_edges(
    "generate", 
    should_continue, 
    {END: END, "reflect": "reflect"}
)

builder.add_edge("planner", "research_plan")
builder.add_edge("research_plan", "generate")

builder.add_edge("reflect", "research_critique")
builder.add_edge("research_critique", "generate")

graph = builder.compile(checkpointer=memory)

# Save the graph to a file and display it
graph_file_path = "graph.png"
graph.get_graph().draw_png(graph_file_path)


from IPython.display import Image

# Display the graph image
Image(graph_file_path)

thread = {"configurable": {"thread_id": "1"}, "recursion_limit": 10}  # Set recursion limit to 10
for s in graph.stream({
    'task': "what is the difference between langchain and langsmith",
    "max_revisions": 2,
    "revision_number": 1,
}, thread):
    print(s)
