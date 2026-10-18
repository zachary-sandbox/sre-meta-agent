import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import asyncio
import json
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.mcp import MCPAdapter
from langchain_core.messages import HumanMessage

# Load environment variables from root .env
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Import graph builder and LLM factory
from app.core.graph import build_graph
from app.services.llm import get_llm

async def main():
    print("[INFO] Starting offline evaluation loop...")
    
    # 1. Load Dataset
    dataset_path = os.path.join(ROOT_DIR, "evals", "dataset.json")
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset not found at: {dataset_path}")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    # 2. Initialize MCP Adapter and Build Graph
    print("[INFO] Connecting to K8s MCP Server...")
    config = {
        "mcpServers": {
            "k8s": {
                "command": "python",
                "args": [str(ROOT_DIR / "mcp_servers" / "k8s_server.py")]
            }
        }
    }
    
    async with MCPAdapter(config) as adapter:
        mcp_tools = await adapter.list_tools()
        print(f"[INFO] Loaded {len(mcp_tools)} tools from MCP.")
        graph = build_graph(mcp_tools)

        # 3. Initialize Judge LLM using the project's Factory
        # This ensures it uses Ollama/DeepSeek/OpenAI based on your .env
        print("[INFO] Initializing Judge LLM...")
        judge_llm = get_llm(temperature=0)
        
        judge_prompt = ChatPromptTemplate.from_template(
            "You are an expert SRE QA evaluator.\n"
            "User Input: {input}\n"
            "Agent Output: {output}\n"
            "Expected Output: {expected}\n"
            "Does the Agent output correctly diagnose the issue based on the expected output? "
            "Return ONLY a valid JSON object with 'score' (0 or 1) and 'reason' (brief explanation)."
        )
        judge_chain = judge_prompt | judge_llm | JsonOutputParser()

        total_score = 0
        results = []

        # 4. Run Evaluation
        for case in dataset:
            print(f"[INFO] Evaluating case: {case['id']}")
            
            config = {"configurable": {"thread_id": f"eval-{case['id']}"}}
            inputs = {"messages": [HumanMessage(content=case["input"])]}
            
            final_output = ""
            # Execute the Agent graph using astream
            async for event in graph.astream(inputs, config=config):
                for node_name, node_state in event.items():
                    if node_state is None:
                        continue
                    if "messages" in node_state:
                        last_msg = node_state["messages"][-1]
                        if hasattr(last_msg, "content") and last_msg.content:
                            if isinstance(last_msg.content, list):
                                final_output = "".join(b.get("text", "") for b in last_msg.content if isinstance(b, dict))
                            else:
                                final_output = str(last_msg.content)

            # 5. Judge the Output
            try:
                eval_result = await judge_chain.ainvoke({
                    "input": case["input"],
                    "output": final_output,
                    "expected": case["expected_output"]
                })
            except Exception as e:
                print(f"[ERROR] Failed to parse Judge output for case {case['id']}: {e}")
                eval_result = {"score": 0, "reason": "Failed to parse JSON from Judge LLM."}

            score = eval_result.get("score", 0)
            reason = eval_result.get("reason", "No reason provided.")
            print(f"[RESULT] Case {case['id']} | Score: {score} | Reason: {reason}")
            
            total_score += score
            results.append(eval_result)

        # 6. Summary
        accuracy = (total_score / len(dataset)) * 100
        print(f"[INFO] Evaluation Complete. Final Accuracy: {accuracy:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())