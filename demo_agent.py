# demo_agents.py

import asyncio
import nest_asyncio
nest_asyncio.apply()

from llama_index.core.agent.workflow import ToolCallResult, AgentStream
from llama_index.tools.duckduckgo import DuckDuckGoSearchToolSpec
from llama_index.tools.wikipedia import WikipediaToolSpec
from llama_index.core.agent.workflow import CodeActAgent
from llama_index.llms.groq import Groq as LlamaGroq
from code_executor import SimpleCodeExecutor

from dotenv import load_dotenv
import pandas as pd
import numpy as np
import datetime
import re
import os

load_dotenv()
MODEL = os.getenv("MODEL")
API_KEY = os.getenv("API_KEY")

llm = LlamaGroq(
    model=MODEL,
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
    "datetime": datetime,
    "pd": pd,
    "np": np,
    "re": re,
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

        # Run async loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._make_inference(query, ctx))

    # Run inference and classify response chunks into text, code and tool 
    async def _make_inference(self, query, ctx):
        handler = self._agent.run(query, ctx=ctx)

        response_chunks = []
        current_text = ""
        buffer = ""

        inside_code = False

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

        output = await handler
        return response_chunks

    def give_instructions(self, instructions):
        self.additional_instructions = instructions