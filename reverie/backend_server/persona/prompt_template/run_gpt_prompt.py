import json
import random
import requests
import time
from utils import *
import openai

# OpenAI Configuration
openai.api_key = openai_api_key

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
        "id": "0586a787-50ae-4a4e-aebe-866cf022aa5b",
        "endpoint": "9ec859b3-9d84-4555-9166-52684d8f6e2f",
        "temperature": 0.9,
        "max_tokens": 1500,
        "top_p": 0.95,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    },
    "analytical": {
        "id": "0586a787-50ae-4a4e-aebe-866cf022aa5b",
        "endpoint": "9ec859b3-9d84-4555-9166-52684d8f6e2f",
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

def safe_generate_response(message, function_name=" ", agent_type="default", repeat=5, fail_safe_response="error", func_validate=None, func_clean_up=None, verbose=False):
    repeat = int(repeat)
    
    if not isinstance(repeat, int):
        raise ValueError(f"Invalid repeat value: {repeat}. It must be an integer.")
    """
    Generates a safe response using LangFlow with optional validation and cleanup.
    """
    if verbose: 
        print(f"Sending message to LangFlow for agent type {agent_type}: {message}")

    flow = AGENT_FLOWS.get(agent_type, AGENT_FLOWS["default"]) if isinstance(agent_type, str) else AGENT_FLOWS["default"]

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
                cleaned_response = func_clean_up(text_response, prompt=message) if func_clean_up else text_response
                
                # Additional parsing for task decomposition
                if function_name == "run_gpt_prompt_task_decomp":
                    try:
                        parsed_response = []
                        for line in cleaned_response.split('\n'):
                            if ') ' in line:
                                task = line.split(') ', 1)[1].split(' (duration')[0].strip()
                                duration = int(line.split('duration in minutes: ')[1].split(',')[0])
                                parsed_response.append([task, duration])
                        return parsed_response
                    except:
                        if verbose:
                            print(f"Failed to parse task decomposition response: {cleaned_response}")
                        continue
                
                return cleaned_response
            
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

def run_gpt_prompt_generate_hourly_schedule(persona, curr_hour_str, n_m1_activity, hour_str, test_input=None):
    """
    Generates an hourly schedule for the persona based on the current hour and other parameters.
    """
    # Implement the logic for generating the hourly schedule here
    # This is a placeholder implementation
    return [f"activity at {curr_hour_str}"]
    """
    Generates a daily plan for the persona based on the wake-up hour.
    """
    # Implement the logic for generating a daily plan here
    # This is a placeholder implementation
    return [f"wake up at {wake_up_hour}:00 and start the day"]
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
