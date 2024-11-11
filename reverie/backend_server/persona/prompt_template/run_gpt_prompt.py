import json
import random
import requests
import time
import os
from utils import *

# LangFlow Configuration
LANGFLOW_BASE_API_URL = "https://api.langflow.astra.datastax.com"
APPLICATION_TOKEN = os.getenv("LANGFLOW_APPLICATION_TOKEN")

# Agent Flow Configuration
AGENT_FLOWS = {
    "default": {
        "id": "0586a787-50ae-4a4e-aebe-866cf022aa5b",
        "endpoint": "9ec859b3-9d84-4555-9166-52684d8f6e2f",
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    },
    "creative": {
        "id": "creative-flow-id",
        "endpoint": "creative-flow-endpoint",
        "temperature": 0.9,
        "max_tokens": 1500,
        "top_p": 0.95,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    },
    "analytical": {
        "id": "analytical-flow-id",
        "endpoint": "analytical-flow-endpoint",
        "temperature": 0.3,
        "max_tokens": 2000,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
    # Add more flows for different agents as needed
}

def temp_sleep(seconds=0.1):
    time.sleep(seconds)

def safe_generate_response(message, agent_type="default", repeat=5, fail_safe_response="error", func_validate=None, func_clean_up=None, verbose=False):
    """
    Generates a safe response using LangFlow with optional validation and cleanup.
    """
    if verbose: 
        print(f"Sending message to LangFlow for agent type {agent_type}: {message}")

    flow = AGENT_FLOWS.get(agent_type, AGENT_FLOWS["default"])

    for attempt in range(repeat): 
        try:
            # Make LangFlow request
            response = LangFlow_request(message, flow)
            
            # Extract text from response
            if isinstance(response, dict) and "outputs" in response:
                try:
                    # Navigate through the response structure to get the text
                    text_response = response["outputs"][0]["output"]
                except (IndexError, KeyError):
                    text_response = str(response)
            else:
                text_response = str(response)

            # Validate and clean up
            if func_validate and func_validate(text_response, prompt=message): 
                return func_clean_up(text_response, prompt=message) if func_clean_up else text_response
            
            if verbose: 
                print(f"---- Repeat count: {attempt}")
                print(text_response)
                print("~~~~")
                
        except Exception as e:
            if verbose:
                print(f"Attempt {attempt} failed with error: {str(e)}")
            continue
            
    return fail_safe_response

def LangFlow_request(message, flow_config):
    """
    Send a request to the LangFlow API with the given prompt and configuration.
    """
    try:
        api_url = f"{LANGFLOW_BASE_API_URL}/lf/{flow_config['id']}/api/v1/run/{flow_config['endpoint']}?stream=false"
        
        payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": {
                "ChatInput-fO1Tz": {},
                "ChatOutput-fIm7Y": {},
                "OpenAIModel-VgBJv": {
                    "temperature": flow_config.get("temperature", 0.7),
                    "max_tokens": flow_config.get("max_tokens", 1000),
                    "top_p": flow_config.get("top_p", 1),
                    "frequency_penalty": flow_config.get("frequency_penalty", 0),
                    "presence_penalty": flow_config.get("presence_penalty", 0)
                },
                "Prompt-tRR6M": {
                    "template": "Respond based on user request:\n\nuser request: {user_request}\n\nResponse:"
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {APPLICATION_TOKEN}",
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

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
