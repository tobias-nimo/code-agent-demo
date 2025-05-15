# demo_agents.py

from llama_index.core.agent.workflow import CodeActAgent
from llama_index.llms.groq import Groq as LlamaGroq
from code_executor import SimpleCodeExecutor

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import datetime
import re

from dotenv import load_dotenv
import os

load_dotenv()
ROOT_MODEL = os.getenv("ROOT_MODEL")
API_KEY = os.getenv("API_KEY")

llm = LlamaGroq(
    model=ROOT_MODEL,
    api_key=API_KEY,
    temperature=0.25,
    top_p=0.9,
    min_p=0,
    top_k=20,
    presence_penalty=0.5
    )
  
code_executor = SimpleCodeExecutor(
    locals={},
    globals={
    "__builtins__": __builtins__,
    "datetime": __import__("datetime"),
    "matplotlib": __import__("matplotlib"),
    "pd": __import__("pandas"),
    "np": __import__("numpy"),
    "re": __import__("re"),
    },
    )

class DemoAgent():
    def __init__(self):
        self._agent = CodeActAgent(
            llm=llm,
            code_execute_fn=code_executor.execute
            #fn=...
            )

        # Default system prompt (for llama models)
        self.system_prompt = f"""
        Cutting Knowledge Date: December 2023
        Today Date: {datetime.datetime.today().strftime("%d %B %Y")}"""

        self.additional_instructions = ""

    def __call__(self, query: str, ctx):

        # Update code-act system prompt
        self._agent.code_act_system_prompt.template += self.system_prompt + self.additional_instructions

        handler = self._agent.run(query, ctx=ctx)
        return handler

    def give_instructions(self, instructions):
        self.additional_instructions = instructions