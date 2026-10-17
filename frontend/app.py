import streamlit as st
import requests
import json
import uuid

# Page configuration
st.set_page_config(page_title="SRE Meta Agent", page_icon="🤖", layout="wide")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "tool_status" not in st.session_state:
    st.session_state.tool_status = ""

# Sidebar: SRE Control Panel Status
with st.sidebar:
    st.header("🎛️ SRE Control Panel")
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}`")
    
    st.subheader("Agent Status")
    status_placeholder = st.empty()
    if st.session_state.tool_status:
        status_placeholder.info(st.session_state.tool_status)
    else:
        status_placeholder.success("Agent Idle")

    st.divider()
    st.subheader("Environment")
    st.markdown("- **Cluster:** `prod-k8s-01`\n- **Namespace:** `payment`")
    st.markdown("---")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Interface: Chat Window
st.title("🚀 SRE Meta Agent (Troubleshooting Copilot)")
st.caption("Enter incident symptoms, and the AI will analyze and invoke K8s tools for troubleshooting.")

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👨‍💻" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("e.g., payment-service-oom keeps restarting, please check the logs..."):
    # 1. Display User Input
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👨‍💻"):
        st.markdown(prompt)

    # 2. Display Agent Response (Streaming)
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Send request to FastAPI SSE endpoint
        url = "http://127.0.0.1:8000/api/v1/chat/stream"
        payload = {"message": prompt, "session_id": st.session_state.session_id}
        
        try:
            # Initiate streaming request using requests
            with requests.post(url, json=payload, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:] # Remove "data: "
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                # Handle Tool Execution Status
                                if data["type"] == "status":
                                    st.session_state.tool_status = data["content"]
                                    status_placeholder.info(data["content"])
                                # Handle LLM Token Stream
                                elif data["type"] == "token":
                                    full_response += data["content"]
                                    message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                pass
            
            # Streaming finished, remove cursor
            message_placeholder.markdown(full_response)
            st.session_state.tool_status = ""
            status_placeholder.success("Analysis Complete")
            
            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

    # 3. HITL (Human-in-the-Loop) Approval Simulation
    # If the Agent suggests a restart, dynamically render an approval card
    if "restart" in full_response.lower():
        with st.container(border=True):
            st.warning("⚠️ **High-Risk Operation Intercepted**: Agent requests to restart Pod `payment-service-error`.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Execution", type="primary", use_container_width=True):
                    st.success("Execution command sent! (In production, this calls the /api/v1/chat/approve endpoint)")
            with col2:
                if st.button("❌ Reject", use_container_width=True):
                    st.info("Operation cancelled.")