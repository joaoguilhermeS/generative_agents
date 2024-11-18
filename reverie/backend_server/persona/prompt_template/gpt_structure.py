import json
import random
import requests
import time
import os
import openai
from utils import *

openai.api_key = openai_api_key

# LangFlow Configuration
LANGFLOW_BASE_API_URL = "http://127.0.0.1:7860"
LANGFLOW_FLOW_ID = "0e3371f1-d48b-47dd-b20f-7a443d784b99"
LANGFLOW_APPLICATION_TOKEN = "sk-ddD9SKkA1TJh4yHngsRsAb2masKeeqviNWMaCGgiAXs"

def temp_sleep(seconds=0.1):
    time.sleep(seconds)

def safe_generate_response(message, agent_type="default", repeat=5, fail_safe_response="error", func_validate=None, func_clean_up=None, verbose=False):
    """
    Generates a safe response using LangFlow with optional validation and cleanup.
    """
    if verbose: 
        print(f"Sending message to LangFlow: {message}")

    for attempt in range(repeat): 
        try:
            # Make LangFlow request
            flow = AGENT_FLOWS.get(agent_type, AGENT_FLOWS.get("default"))
            # Add the rest of the logic for handling the flow here
            # For now, let's just simulate a response
            response = LangFlow_request(message)
            if func_validate and func_validate(response):
                return func_clean_up(response)
        except Exception as e:
            if verbose:
                print(f"Attempt {attempt} failed with error: {str(e)}")
            continue

def LangFlow_request(message):
    """
    Send a request to the LangFlow API with the given prompt.
    """
    try:
        api_url = f"{LANGFLOW_BASE_API_URL}/api/v1/run/{LANGFLOW_FLOW_ID}?stream=false"
        
        payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": {
                "ChatInput-Yqb6n": {},
                "ChatOutput-wSm2d": {},
                "OpenAIModel-sOWWG": {},
                "Prompt-MJkDg": {
                    "template": "Respond based on user request:\n\nuser request: {user_request}\n\nResponse:"
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {LANGFLOW_APPLICATION_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"LangFlow API Error: {str(e)}")
        return {"error": str(e)}




    except requests.exceptions.RequestException as e:
        print(f"LangFlow API Error: {str(e)}")
        return {"error": str(e)}

def generate_prompt(curr_input, prompt_lib_file):
    """
    Generates the final prompt by replacing placeholders in the prompt template with actual inputs.
    """
    if isinstance(curr_input, str):
        curr_input = [curr_input]
    else:
        curr_input = [str(i) for i in curr_input]

    with open(prompt_lib_file, "r") as f:
        prompt = f.read()

    for count, item in enumerate(curr_input):   
        prompt = prompt.replace(f"!<INPUT {count}>!", item)
        
    if "<commentblockmarker>###</commentblockmarker>" in prompt: 
        prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
        
    return prompt.strip()

def get_embedding(text, model="text-embedding-ada-002"):
    """
    Generates an embedding for the given text using OpenAI's embedding API.
    """
    text = text.replace("\n", " ")
    if not text: 
        text = "this is blank"
    return openai.Embedding.create(
            input=[text], model=model)['data'][0]['embedding']

if __name__ == '__main__':
    message = "driving to a friend's house"
    prompt_lib_file = "prompt_template/test_prompt_July5.txt"
    prompt = generate_prompt(message, prompt_lib_file)

    def __func_validate(langflow_response):
        if "error" in langflow_response:
            return False
        return True

    def __func_clean_up(langflow_response):
        return langflow_response.get("output", "error")

    output = safe_generate_response(
        message=prompt,
        repeat=5,
        fail_safe_response="rest",
        func_validate=__func_validate,
        func_clean_up=__func_clean_up,
        verbose=True
    )

    print(output)
