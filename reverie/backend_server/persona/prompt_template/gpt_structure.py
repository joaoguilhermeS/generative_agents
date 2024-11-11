"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling OpenAI APIs.
"""
import json
import random
import time 
from utils import *
from .run_gpt_prompt import safe_generate_response

def temp_sleep(seconds=0.1):
  time.sleep(seconds)

def ChatGPT_single_request(prompt, agent_type="default"): 
  temp_sleep()
  return safe_generate_response(prompt, agent_type)

# ============================================================================
# #####################[SECTION 1: CHATGPT-3 STRUCTURE] ######################
# ============================================================================

def GPT4_request(prompt, agent_type="default"): 
  """
  Given a prompt, make a request to LangFlow and returns the response. 
  ARGS:
    prompt: a str prompt
    agent_type: the type of agent to use (default or others defined in AGENT_FLOWS)
  RETURNS: 
    a str of LangFlow's response. 
  """
  temp_sleep()
  try: 
    return safe_generate_response(prompt, agent_type)
  except: 
    print ("LangFlow ERROR")
    return "LangFlow ERROR"

def ChatGPT_request(prompt, agent_type="default"): 
  """
  Given a prompt, make a request to LangFlow and returns the response. 
  ARGS:
    prompt: a str prompt
    agent_type: the type of agent to use (default or others defined in AGENT_FLOWS)
  RETURNS: 
    a str of LangFlow's response. 
  """
  try: 
    return safe_generate_response(prompt, agent_type)
  except: 
    print ("LangFlow ERROR")
    return "LangFlow ERROR"

def GPT4_safe_generate_response(prompt, 
                                example_output,
                                special_instruction,
                                repeat=3,
                                fail_safe_response="error",
                                func_validate=None,
                                func_clean_up=None,
                                verbose=False,
                                agent_type="default"): 
  prompt = 'LangFlow Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt += f"{special_instruction}\n"
  prompt += f"Example output: {str(example_output)}"

  if verbose: 
    print ("LANGFLOW PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_response = GPT4_request(prompt, agent_type).strip()
      
      if func_validate(curr_response, prompt=prompt): 
        return func_clean_up(curr_response, prompt=prompt) if func_clean_up else curr_response
      
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_response)
        print ("~~~~")

    except Exception as e: 
      if verbose:
        print(f"Error in GPT4_safe_generate_response: {str(e)}")
      pass

  return fail_safe_response

def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False,
                                   agent_type="default"): 
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"{special_instruction}\n"
  prompt += f"Example output: {str(example_output)}"

  if verbose: 
    print ("LANGFLOW PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_response = ChatGPT_request(prompt, agent_type).strip()
      
      if func_validate(curr_response, prompt=prompt): 
        return func_clean_up(curr_response, prompt=prompt) if func_clean_up else curr_response
      
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_response)
        print ("~~~~")

    except Exception as e: 
      if verbose:
        print(f"Error in ChatGPT_safe_generate_response: {str(e)}")
      pass

  return fail_safe_response

def generate_prompt(curr_input, prompt_lib_file): 
  """
  Takes in the current input (e.g. comment that you want to classifiy) and 
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this 
  function replaces this substr with the actual curr_input to produce the 
  final promopt that will be sent to the LangFlow server. 
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file. 
  RETURNS: 
    a str prompt that will be sent to LangFlow server.  
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()

def safe_generate_response(prompt, 
                           agent_type="default",
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if verbose: 
    print(f"Sending prompt to LangFlow for agent type {agent_type}: {prompt}")

  flow = AGENT_FLOWS.get(agent_type, AGENT_FLOWS["default"])

  for attempt in range(repeat): 
    try:
      response = ChatGPT_request(prompt, agent_type)
      
      if func_validate and func_validate(response, prompt=prompt): 
        return func_clean_up(response, prompt=prompt) if func_clean_up else response
      
      if verbose: 
        print(f"---- Repeat count: {attempt}")
        print(response)
        print("~~~~")
        
    except Exception as e:
      if verbose:
        print(f"Attempt {attempt} failed with error: {str(e)}")
      continue
      
  return fail_safe_response

if __name__ == '__main__':
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(response): 
    if len(response.strip()) <= 1:
      return False
    if len(response.strip().split(" ")) > 1: 
      return False
    return True
  def __func_clean_up(response):
    cleaned_response = response.strip()
    return cleaned_response

  output = safe_generate_response(prompt, 
                                 "default",
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)




















