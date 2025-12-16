# manual COT
import requests
from openai import OpenAI
import json
from pydantic import BaseModel, Field
import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key= os.getenv('GROQ_API_KEY'),
    base_url= "https://api.groq.com/openai/v1"
)

def weatherget(city:str):
    url = f"https://wttr.in/{city.lower()}?format=%C%t"
    responseWeather = requests.get(url)

    if responseWeather.status_code == 200:
        return f"the weather in {city} is {responseWeather.text}"

available_tools = {
    "weatherget" : weatherget
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
- Only run 1 step at a time.
- The sequence of a step is START( where user gives an input ), PLAN (That can be multiple times) and finally OUTPUT which is going to be displayed to the user.
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
3. End with OUTPUT only when fully solved

OUTPUT JSON FORMAT:
{"step": "START" | "PLAN" | "OUTPUT" , "content" : "string"}

Available Tools:
- weatherget(city: str) : Takes city name as an input string and returns the weather information about the city

Example 1:
user query: Can you solve 2+3*5/10?
START: {"step":"START" , "content" : "Seems like user is interested in maths problem" }
PLAN: {"step":"PLAN" , "content" : "Looking at the problem, we should solve this using BODMAS method" }
PLAN: {"step":"PLAN" , "content" : "Yes, The BODMAS is correct thing done here" }
PLAN: {"step":"PLAN" , "content" : "First we should multiply 3*5 which is 15" }
PLAN: {"step":"PLAN" , "content" : "Now the new equation is 2+15/10" }
PLAN: {"step":"PLAN" , "content" : "We must perform divide on 15/10 which is 1.5" }
PLAN: {"step":"PLAN" , "content" : "Now the new equation is 2+1.5" }
PLAN: {"step":"PLAN" , "content" : "We must perform addition on 2+1.5 which is 3.5" }
PLAN: {"step":"PLAN" , "content" : "Great, we has solved and finally left with 3.5 as ans" }
OUTPUT: {"step":"OUTPUT", "content": "3.5"}


Example 2:
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

user_query = input(">> ")
message_history.append({"role":"user", "content": user_query})



while True:
    response = client.chat.completions.create(
        model="groq/compound-mini",
        response_format={
        "type": "json_object"
    },
        temperature=0,
        messages=message_history
    )
    raw_content = response.choices[0].message.content
    parsed_response = json.loads(raw_content)

# Optional: validate with Pydantic
    validated = LLM_OUTPUT(**parsed_response)

    # save assistant response
    message_history.append({
        "role": "assistant",
        "content": raw_content
    })

    

    if validated.step == "START":
        print("START:", validated.content)

        # ask model to continue
        message_history.append({
            "role": "user",
            "content": "Continue to the next step."
        })

    if validated.step == "PLAN":
        print("PLAN:", validated.content)

        message_history.append({
            "role": "user",
            "content": "Continue to the next step."
        })

    if validated.step == "TOOL":
        tool_name = validated.tool
        tool_input = validated.input

        tool_output = available_tools[tool_name](tool_input)
        print(f"TOOL CALL: {tool_name}({tool_input}) → {tool_output}")

        # OBSERVE must be injected as USER or SYSTEM (NOT developer)
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
    message_history.append({
        "role": "user",
        "content": "Continue with the next step."
    })



