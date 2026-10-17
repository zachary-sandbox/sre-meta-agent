import streamlit as st
import requests
import json
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default backend URL if not set in .env
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# Page configuration
st.set_page_config(page_title="SRE Meta Agent", layout="wide")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "tool_status" not in st.session_state:
    st.session_state.tool_status = ""
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False

# ==========================================
# Helper: Handle SSE Stream
# ==========================================
def process_stream(endpoint, payload, message_placeholder, status_placeholder):
    url = f"{BACKEND_URL}/api/v1/{endpoint}"
    full_response = ""
    
    try:
        with requests.post(url, json=payload, stream=True, timeout=120) as response:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:] 
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if data["type"] == "status":
                                st.session_state.tool_status = data["content"]
                                status_placeholder.info(data["content"])
                                message_placeholder.markdown(f"*{data['content']}*")
                            
                            elif data["type"] == "token":
                                full_response += data["content"]
                                message_placeholder.markdown(full_response + "|") 
                            
                            elif data["type"] == "approval":
                                st.session_state.pending_approval = True
                                st.session_state.tool_status = "[WARN] Waiting for SRE approval..."
                                status_placeholder.warning(st.session_state.tool_status)
                                return None
                                
                            elif data["type"] == "error":
                                st.error(f"[ERROR] Backend Error: {data['content']}")
                                return None
                                
                        except json.JSONDecodeError:
                            pass
        
        if full_response:
            message_placeholder.markdown(full_response)
        return full_response
        
    except Exception as e:
        st.error(f"[ERROR] Failed to connect to backend: {e}")
        return None

# Sidebar
with st.sidebar:
    st.header("[SRE] Control Panel")
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}`")
    
    st.subheader("Agent Status")
    status_placeholder = st.empty()
    if st.session_state.tool_status:
        status_placeholder.info(st.session_state.tool_status)
    else:
        status_placeholder.success("[INFO] Agent Idle")

    st.divider()
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_approval = False
        st.rerun()

# Main Interface
st.title("[SRE] Meta Agent (Troubleshooting Copilot)")

# Render Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# HITL Approval UI
if st.session_state.pending_approval:
    with st.container(border=True):
        st.warning("[WARN] **HITL Intercept**: Agent requests a high-risk K8s operation.")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("[APPROVE] Execute", type="primary", use_container_width=True):
                st.session_state.pending_approval = False
                with st.chat_message("assistant", avatar="assistant"):
                    msg_ph = st.empty()
                    payload = {"message": "resume", "session_id": st.session_state.session_id}
                    final_text = process_stream("chat/approve?approved=true", payload, msg_ph, status_placeholder)
                    if final_text:
                        st.session_state.messages.append({"role": "assistant", "content": final_text})
                st.rerun()
                
        with col2:
            if st.button("[REJECT] Cancel", use_container_width=True):
                st.session_state.pending_approval = False
                with st.chat_message("assistant", avatar="assistant"):
                    msg_ph = st.empty()
                    payload = {"message": "resume", "session_id": st.session_state.session_id}
                    final_text = process_stream("chat/approve?approved=false", payload, msg_ph, status_placeholder)
                    if final_text:
                        st.session_state.messages.append({"role": "assistant", "content": final_text})
                st.rerun()

# Chat Input
if prompt := st.chat_input("e.g., payment-service-oom keeps restarting, please check the logs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="assistant"):
        message_placeholder = st.empty()
        payload = {"message": prompt, "session_id": st.session_state.session_id}
        
        final_text = process_stream("chat/stream", payload, message_placeholder, status_placeholder)
        
        if final_text:
            st.session_state.messages.append({"role": "assistant", "content": final_text})
            st.session_state.tool_status = ""
            status_placeholder.success("[INFO] Analysis Complete")
        
        if st.session_state.pending_approval:
            st.rerun()