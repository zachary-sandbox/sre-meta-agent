import sys
import os
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from app.services.llm import llm

@tool
def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    """Retrieve K8s logs for a specific Pod and namespace."""
    return f"Mock logs for {pod_name} in {namespace}: Container OOMKilled."

def main():
    print("[INFO] Starting local LLM debugging script...")
    print(f"[INFO] Current Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"[INFO] Current Model: {os.getenv('LLM_MODEL_NAME')}")

    # 1. Test basic chat
    print("\n[TEST] 1. Testing basic LLM connection...")
    try:
        response = llm.invoke([HumanMessage(content="Hello, who are you?")])
        print(f"[SUCCESS] Basic Chat Response:\n{response.content}")
    except Exception as e:
        print(f"[ERROR] Failed basic connection: {e}")
        return

    # 2. Test Tool Calling Capability
    print("\n[TEST] 2. Testing Tool Calling capability...")
    llm_with_tools = llm.bind_tools([get_pod_logs])
    prompt = "The pod 'payment-service-oom' is crashing. I need to check its logs."
    
    try:
        response_with_tools = llm_with_tools.invoke([HumanMessage(content=prompt)])
        
        if getattr(response_with_tools, "tool_calls", None):
            print("[SUCCESS] The model decided to call a tool:")
            print(f"  Tool Name: {response_with_tools.tool_calls[0]['name']}")
            print(f"  Arguments: {response_with_tools.tool_calls[0]['args']}")
        else:
            print("[WARN] The model did not trigger a tool call.")
            print(f"  Raw response: {response_with_tools.content}")
            print("  Tip: Try a larger model like 'llama3.1' or 'qwen2.5:7b' if this fails.")
    except Exception as e:
        print(f"[ERROR] Failed tool calling test: {e}")

if __name__ == "__main__":
    main()