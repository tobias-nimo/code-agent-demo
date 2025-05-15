# app.py

from llama_index.core.agent.workflow import ToolCallResult, AgentStream
from llama_index.core.workflow import Context

from demo_agent import DemoAgent
from multimodal import stt

from streamlit_mic_recorder import mic_recorder
import streamlit as st

import tempfile
import asyncio
import time
import json
import os
import io

# Set page title and favicon
st.set_page_config(
    page_title="Demo Time",
    page_icon="✨"
)

# Make it look pretty :)
css = """
<style>
/* Sidebar background and border */
section[data-testid="stSidebar"] {
  background-color: #12131A;
  border-right: 1px solid #2F323C;
}
/* Center the title */
.centered-title {
  text-align: center;
  font-size: 2.5em;
  font-weight: bold;
  margin-bottom: 40px;
}
/* Fix chat container to properly display messages in correct order */
[data-testid="stChatMessageContent"] {
  width: 100%;
}
</style>

<div class="centered-title">Hello there... 👋</div>
"""

st.markdown(css, unsafe_allow_html=True)

# Session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = DemoAgent()

if "memory" not in st.session_state:
    st.session_state.memory = {}

if "processing_query" not in st.session_state:
    st.session_state.processing_query = False

if "voice_input_key" not in st.session_state:
    st.session_state.voice_input_key = 0

context = Context(st.session_state.agent._agent)

# Create the chat container first
chat_container = st.container()

# Create the input area at the bottom
input_container = st.container()

# Define the sidebar content
with st.sidebar:
    # File uploader
    uploaded_files = st.file_uploader(label="📂 Uploaded Files", type=None, accept_multiple_files=True, label_visibility="visible")

    # Handle files
    temp_file_paths = []
    if uploaded_files:
        # Make temp dirs
        temp_dir = tempfile.mkdtemp()
        for file in uploaded_files:
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.read())
            temp_file_paths.append(file_path)

        # Update agent's prompt
        file_list = '\n'.join(f'- {file}' for file in temp_file_paths)
        instructions = f"""
        The user has uploaded the following files:
        {file_list}"""
        st.session_state.agent.give_instructions(instructions)

    # Action buttons below chat input
    with st.container():
        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🌐", help="Web-search mode", use_container_width=True):
                st.warning("WIP")

        with col2:
            if st.button("💡", help="Reasoning mode", use_container_width=True):
                st.warning("WIP")

# Display chat messages from session state in the chat container
with chat_container:
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            # Multi-chunk assistant message
            if isinstance(msg["content"], list):
                for chunk in msg["content"]:
                    if chunk["type"] == "text":
                        st.markdown(chunk["content"])
                    elif chunk["type"] == "code":
                        with st.expander("🛠️ Code", expanded=False):
                            st.code(chunk["content"], language="python")
                    elif chunk["type"] == "tool":
                        with st.expander("⚙️ Output", expanded=False):
                            st.code(chunk["content"], language="raw")
            # Regular user message
            else:
                st.markdown(msg["content"])

# Put the input elements at the bottom
with input_container:
    col1, col2, col3 = st.columns([86, 7, 7])
    with col1:
        # Chat bar
        query = st.chat_input("Ask me anything...")

    with col2:
        # Audio recorder
        audio_data = mic_recorder(
            start_prompt="🗣️",
            stop_prompt="⏹️",
            just_once=True,
            use_container_width=True,
            key=f"voice_input_{st.session_state.voice_input_key}"
        )
    with col3:
        if st.session_state.get("messages"):
            if st.button("🗑️", help="Restart chat", use_container_width=True):
                # Generate a new unique key for the voice recorder widget and store it temporarily 
                st.session_state.voice_input_key += 1
                value_to_keep = st.session_state.get("voice_input_key") 

                # Clear everything in state memory, but restore important keys
                st.session_state.clear()
                if value_to_keep is not None: st.session_state["voice_input_key"] = value_to_keep

                st.rerun()

# Process audio input if present
if audio_data:
    audio_bytes = audio_data["bytes"]
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "input.wav"
    query = stt(audio_file)

# Process text input if present
if query and not st.session_state.processing_query:    
    # Set processing flag
    st.session_state.processing_query = True

    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Override context with session state memory
    if st.session_state.memory:
        context = Context.from_dict(
            workflow=st.session_state.agent._agent,
            data=st.session_state.memory
        )
        
    async def run_inference(query, ctx):
        response_chunks = []
        current_text = ""
        buffer = ""

        inside_code = False

        # Run inference
        handler = st.session_state.agent(query, ctx)

        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                buffer += event.delta

                while "<execute>" in buffer and "</execute>" in buffer:
                    before, rest = buffer.split("<execute>", 1)
                    code, after = rest.split("</execute>", 1)

                    current_text += before
                    if current_text.strip():
                        response_chunks.append({"type": "text", "content": current_text.strip()})
                        current_text = ""

                    response_chunks.append({"type": "code", "content": code.strip()})
                    buffer = after

            elif isinstance(event, ToolCallResult):
                if buffer.strip():
                    response_chunks.append({"type": "text", "content": buffer.strip()})
                    buffer = ""

                tool_result = str(event.tool_output).strip()
                response_chunks.append({"type": "tool", "content": tool_result})

        if buffer.strip():
            response_chunks.append({"type": "text", "content": buffer.strip()})

        _ = await handler
        return response_chunks

    # Run inference async loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response_chunks = loop.run_until_complete(run_inference(query, ctx=context))
    
    # Add assistant response to state
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_chunks
    })
            
    # Note: context can not be stored as session var due to streamlit async incompatibility.
    # As a work-around, I transform context into a dict and store it as session var at the end of the st loop. 
    st.session_state.memory = context.to_dict()

    # Reset processing flag
    st.session_state.processing_query = False

    # Force rerun to update UI with new messages
    st.rerun()