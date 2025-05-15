# app.py

import asyncio
import nest_asyncio
nest_asyncio.apply()

from llama_index.core.workflow import Context
from demo_agent import DemoAgent

from streamlit_mic_recorder import mic_recorder
import streamlit as st
import tempfile
import asyncio
import time
import json
import os

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
  margin-bottom: 30px;
}
/* Fix chat container to properly display messages in correct order */
[data-testid="stChatMessageContent"] {
  width: 100%;
}
/* Auto-scroll to bottom script */
div[data-testid="stVerticalBlock"] {
  max-height: none !important;
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
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🌐", help="Web-search mode", use_container_width=True):
                st.warning("WIP")

        with col2:
            if st.button("💡", help="Reasoning mode", use_container_width=True):
                st.warning("WIP")

        with col3:
            if st.button("🔍", help="Vision mode", use_container_width=True):
                st.warning("WIP")

        with col4:
            if st.session_state.get("messages"):
                if st.button("❌", help="Restart chat", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()

# Display chat messages in the chat container
with chat_container:
    # Display messages from session state
    for msg in st.session_state.get("messages", []):
        with st.chat_message(msg["role"]):
            if isinstance(msg["content"], list):
                # Multi-chunk assistant message
                for chunk in msg["content"]:
                    if chunk["type"] == "text":
                        st.markdown(chunk["content"])
                    elif chunk["type"] == "code":
                        with st.expander("🛠️ Code", expanded=False):
                            st.code(chunk["content"], language="python")
                    elif chunk["type"] == "tool":
                        with st.expander("⚙️ Output", expanded=False):
                            st.code(chunk["content"], language="raw")
            else:
                # Regular message
                st.markdown(msg["content"])

# Put the input elements at the bottom
with input_container:
    col1, col2 = st.columns([93, 7])
    with col1:
        # Chat bar
        query = st.chat_input("Ask me anything...")

    with col2:
        # Audio recorder
        audio_data = mic_recorder(
            start_prompt="🗣️",
            stop_prompt="🟥",
            just_once=True,
            use_container_width=False,
            key="voice_input"
        )

# Process audio input if present
if audio_data:
    pass
    # TODO: use whisper to process audio_data

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
    
    # Get response
    response_chunks = st.session_state.agent(query, context)
    
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