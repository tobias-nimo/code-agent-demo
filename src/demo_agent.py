# demo_agent.py

from llama_index.core.agent.workflow import CodeActAgent
from llama_index.llms.groq import Groq as LlamaGroq

from base_tools import transcribe_audio, analyze_image
from code_executor import SimpleCodeExecutor

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import re

from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()
SYSTEM_PROMPT_KEY = os.getenv("SYSTEM_PROMPT_KEY")
API_KEY = os.getenv("API_KEY")
LLM = os.getenv("LLM")

# LLM
llm = LlamaGroq(
    api_key=API_KEY,
    model=LLM,
    presence_penalty=0.5,
    temperature=0.25,
    top_p=0.9,
    top_k=20,
    min_p=0,
    )

# Code executor
code_executor = SimpleCodeExecutor(
    locals={
    "transcribe_audio": transcribe_audio,
    "analyze_image": analyze_image
    },
    globals={
    "__builtins__": __builtins__,
    "datetime": __import__("datetime"),
    "matplotlib": __import__("matplotlib"),
    "pd": __import__("pandas"),
    "np": __import__("numpy"),
    "re": __import__("re"),
    },
    )

# System prompt
current_dir = Path(__file__).parent
file_path = current_dir.parent / "prompts" / (SYSTEM_PROMPT_KEY+".txt")

with open(file_path, "r") as file: content = file.read()
system_prompt = eval(f"f'''{content}'''")

## Agent Workflow ##
class DemoAgent():
    def __init__(self):
        self._agent = CodeActAgent(
            llm=llm,
            code_execute_fn=code_executor.execute,
            tools=[transcribe_audio, analyze_image]
            )

        self.system_prompt = system_prompt

        self.additional_instructions = ""

    def __call__(self, query: str, ctx):

        # Update code-act system prompt
        self._agent.code_act_system_prompt.template += self.system_prompt + self.additional_instructions

        handler = self._agent.run(query, ctx=ctx)
        return handler

    def give_instructions(self, instructions):
        self.additional_instructions = instructions