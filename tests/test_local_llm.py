import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm import llm
from app.tools.k8s_tools import get_pod_logs
from langchain_core.messages import HumanMessage

print("🔍 Testing LLM Connection...")
# 1. Test basic chat
response = llm.invoke([HumanMessage(content="Hello, who are you?")])
print(f"✅ Basic Chat Response:\n{response.content}\n")

print("🔍 Testing Tool Calling Capability...")
# 2. Test Tool Calling
llm_with_tools = llm.bind_tools([get_pod_logs])

# Force the model to think about a tool call
prompt = "The pod 'payment-service-oom' is crashing. I need to check its logs."
response_with_tools = llm_with_tools.invoke([HumanMessage(content=prompt)])

if response_with_tools.tool_calls:
    print("✅ SUCCESS! The local model decided to call a tool:")
    print(f"Tool Name: {response_with_tools.tool_calls[0]['name']}")
    print(f"Arguments: {response_with_tools.tool_calls[0]['args']}")
else:
    print("❌ WARNING: The model did not trigger a tool call.")
    print(f"Raw response: {response_with_tools.content}")
    print("💡 Tip: Try a larger model like 'llama3.1' or 'qwen2.5:7b' if this fails.")