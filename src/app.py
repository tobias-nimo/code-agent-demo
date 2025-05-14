# app.py

import asyncio
import nest_asyncio
nest_asyncio.apply()

from llama_index.core.workflow import Context
from demo_agent import DemoAgent

import streamlit as st
import tempfile
import asyncio
import time
import json
import os

st.set_page_config(page_title="Demo Time", layout="wide")
st.title("Hello 👋")

# Session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = DemoAgent()

if "memory" not in st.session_state:
    st.session_state.memory = {}

context = Context(st.session_state.agent._agent)

# Display messages
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

# Input and chat logic
if query := st.chat_input("Ask me anything..."):

    st.chat_message("user").markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Override context with session state memory
    if st.session_state.memory:
        context = Context.from_dict(
            workflow=st.session_state.agent._agent,
            data=st.session_state.memory
            )

    # Inference
    response_chunks = st.session_state.agent(query, context)

    # Display message immediately
    with st.chat_message("assistant"):
        for chunk in response_chunks:
            if chunk["type"] == "text":
                st.markdown(chunk["content"])

            elif chunk["type"] == "code":
                with st.expander("🛠️ Code", expanded=False):
                   st.code(chunk["content"], language="python")

            elif chunk["type"] == "tool":
                with st.expander("⚙️ Output", expanded=False):
                   st.code(chunk["content"], language="raw")

    # Store full structured response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_chunks
    })

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
            if st.button("👀", help="Vision mode", use_container_width=True):
                st.warning("WIP")

        with col4:
            if st.session_state.get("messages"):
                if st.button("🔁", help="Restart Chat", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()

# Note: context can not be stored as session var due to streamlit asyn incompatibility.
# As a work-around, I store transform context into a dict and store that as session var at the end each iterarion. 
st.session_state.memory = context.to_dict()