
from openai import OpenAI
import json
from pydantic import BaseModel, Field
import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key= os.getenv('GEMINI_API_KEY'),
    base_url= "https://generativelanguage.googleapis.com/v1beta/openai/"
)

    
def run_cmd(cmd:str):
    result = os.system(cmd)
    return result


available_tools = {
    "run_cmd" : run_cmd
}

SYSTEM_PROMPT = '''
You are an expert AI assistant in resolving user queries using chain of thought .
You work on START, PLAN and OUTPUT , TOOL and OBSERVE steps.
You need to first PLAN what needs to be done. The PLAN can be multiple steps.
Once you think enough PLAN has been done, finally you can give an OUTPUT.
you can also call a tool if required from the list of available tools.
For every tool call, wait for the OBSERVE step which is the output from the called tool. 


Rules:
- Strictly follow the given JSON format.
- The sequence of a step is START( where user gives an input ), PLAN (That can be multiple times), TOOL, OBSERVE finally OUTPUT which is going to be displayed to the user.
- you can also call a tool if required from the list of available tools
You are an expert AI assistant that solves problems using
EXPLICIT STEP EXECUTION.

You MUST respond in EXACTLY ONE STEP per message.

Allowed steps:
- START: understand the problem
- PLAN: describe ONE next step to solve it
- TOOL : you can also call a tool if required from the list of available tools
- OBSERVE
- OUTPUT: give the final answer


Rules:
- You must NEVER skip steps
- You must NEVER jump directly to OUTPUT
- Each response must contain ONLY ONE step
- Follow the JSON format strictly
- STRICTLY FOLLOW THE ORDER
- DO PROPER THINKING ACCORDING TO THE EXAMPLES.
- GIVE RESPONSES AS SPECIFIED IN THE EXAMPLES.
- DONT GIVE WEATHER RESPONSE ON THE BASE OF YOUR DATA, just return the tool
- “You MUST respond in EXACTLY ONE STEP per message”
- You should follow steps in order otherwise we will not use your service and unsubscribe your service.
- If in any task by chance there is no output step, you should generate OUTPUT, by writing any sentence related to it

Full order : START -> PLAN -> OBSERVE -> TOOL -> OUTPUT

JSON FORMAT:
{
  "step": "START" | "PLAN" | "OUTPUT" | TOOL,
  "content": "string",
  "tool": "string",
  "input" : "string"
}

Workflow:
1. First response MUST be START
2. Then multiple PLAN responses (one step at a time)
3. Tools to be called if any
4. End with OUTPUT only when fully solved

OUTPUT JSON FORMAT:
{"step": "START" | "PLAN" | "OUTPUT" , "content" : "string"}

Available Tools:
- run_cmd(cmd:str) : Takes a system linux command as string and executes the command on user's system and returns the output from that command
-- def run_cmd(cmd:str):
    result = os.system(cmd)
    return result



Example :
user query: What is the weather of delhi?
START: {"step":"START": , "content" : "Seems like user is interested in getting the weather of delhi in India" }
PLAN: {"step":"PLAN":  "content" : "Lets see if we have any available tool from the list of available tools" }
PLAN: {"step":"PLAN":  "content" : "Great, we have weatherget tool available for this query" }
PLAN: {"step":"PLAN":  "content" : "I need to call get weather tool for delhi as input for city" }
PLAN: {"step":"TOOL": "tool": "weatherget" , "content" : "delhi" }
PLAN: {"step":"OBSERVE": "tool": "weatherget" , "output" : "the temperature of delhi : " }
PLAN: {"step":"PLAN":  "content" : "Great, I got the weather info about delhi" }

-----

RESPONSE SEQUENCE:
1. START
2. PLAN
3. TOOL
4. OUTPUT
The above sequence should be STRICTLY FOLLOWED
Until and unless 1 state is not over, you should not move to another state without giving the OUTPUT step
PLEASE FOLLOW THE ABOVE SEQUENCE ONLY
'''


class LLM_OUTPUT(BaseModel):
    step: str = Field(..., description="The ID of the step, Example: START, PLAN, TOOL, OUTPUT, etc"),
    content: Optional[str] = Field(None, description="The optional string content for the step")
    tool: Optional[str] = Field(None, description="The ID of the tool to be called")
    input: Optional[str] = Field(None, description="The input params for the tool")


print("\n\n\n")

message_history = [
      {"role":"system", "content": SYSTEM_PROMPT} 
]
def takeQuery():

    user_query = input(">> ")
    message_history.append({"role":"user", "content": user_query})

takeQuery()
while True:
    

    
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        response_format={
        "type": "json_object"
    },
        temperature=0,
        messages=message_history
    )
    raw_content = response.choices[0].message.content
    parsed_response = json.loads(raw_content)
    validated = LLM_OUTPUT(**parsed_response)
    message_history.append({
        "role": "assistant",
        "content": raw_content
    })

    

    if validated.step == "START":
        print("START:", validated.content)

    if validated.step == "PLAN":
        print("PLAN:", validated.content)


    if validated.step == "TOOL":
        tool_name = validated.tool
        tool_input = validated.input

        tool_output = available_tools[tool_name](tool_input)
        print(f"TOOL CALL: {tool_name}({tool_input}) → {tool_output}")
        message_history.append({
            "role": "user",
            "content": json.dumps({
                "step": "OBSERVE",
                "tool": tool_name,
                "input": tool_input,
                "output": tool_output
            })
        })

    elif validated.step == "OUTPUT":
        print("OUTPUT:", validated.content)
        break
        



