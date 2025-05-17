# demo_agent.py

from dotenv import load_dotenv
from pathlib import Path
import importlib
import warnings
import inspect
import sys
import os

from llama_index.core.agent.workflow import CodeActAgent
from llama_index.llms.groq import Groq as LlamaGroq

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import re

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.code_executor import SimpleCodeExecutor

# Load env variavbles
load_dotenv()
AGENT_NAME = os.getenv("AGENT_NAME", "base")
GROK_API_KEY = os.getenv("GROK_API_KEY")
LLM = os.getenv("LLM")

# LLM
llm = LlamaGroq(
    api_key=GROK_API_KEY,
    model=LLM,
    #presence_penalty=0.5,
    #temperature=0.25,
    #top_p=0.9,
    #top_k=20,
    #min_p=0,
    )

def load_agent_tools():
    """Load agent tools."""
    def get_module_functions(module_name):
        try:
            mod = importlib.import_module(module_name)
            return {
                name: obj for name, obj in inspect.getmembers(mod, inspect.isfunction)
                if obj.__module__ == mod.__name__
            }
        except ModuleNotFoundError:
            warnings.warn(f"[WARN] Module '{module_name}' not found.")
            return {}

    # Always load base tools
    tools_dict = get_module_functions("tools.base_tools")

    # Load custom tools if AGENT_NAME is set
    if AGENT_NAME != "base":
        custom_module = f"tools.custom_tools_{AGENT_NAME}"
        custom_tools = get_module_functions(custom_module)

        # Override or extend the base tools
        tools_dict.update(custom_tools)
    else: 
        warnings.warn(f"[WARN] Base agent has no custom tools.")

    return tools_dict

def build_code_executor_fn():
    """Build code executor function."""
    code_executor = SimpleCodeExecutor(
        locals=load_agent_tools(),
        globals={
        "__builtins__": __builtins__,
        "datetime": __import__("datetime"),
        "matplotlib": __import__("matplotlib"),
        "pd": __import__("pandas"),
        "np": __import__("numpy"),
        "re": __import__("re"),
        },
        )
    return code_executor.execute

def get_system_prompt():
    """Load and format system prompt."""
    current_dir = Path(__file__).parent
    file_path = current_dir.parent / "prompts" / (AGENT_NAME+".txt")
    try:
        with open(file_path, "r") as file: 
            content = file.read()
        return eval(f"f'''{content}'''")
    except Exception as e:
        warnings.warn(f"[WARN] Could not load system prompt: {str(e)}")
        return ""

## Agent Workflow ##
class DemoAgent():
    def __init__(self):
        self._agent = CodeActAgent(
            llm=llm,
            code_execute_fn=build_code_executor_fn(),
            tools=list(load_agent_tools().values())
            )

        self.system_prompt = get_system_prompt()

        self.additional_instructions = ""

    def __call__(self, query: str, ctx):

        # Update code-act system prompt
        self._agent.code_act_system_prompt.template += self.system_prompt + self.additional_instructions

        handler = self._agent.run(query, ctx=ctx)
        return handler

    def give_instructions(self, instructions):
        self.additional_instructions = instructions