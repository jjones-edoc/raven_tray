import os
import re


def read_prompt_from_file(filename):
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(script_dir, 'prompts', filename)
    with open(file_path, 'r') as file:
        return file.read().strip()


def clean_string(arg):
    return arg.strip().strip('"').strip("'")


def extract_function_call(ai_response):
    # Regular expression to capture the function call and its arguments
    pattern = r"(\w+)\((.*?)\)"

    # Search for the function call in the AI response
    match = re.search(pattern, ai_response)

    if match:
        function_name = match.group(1)
        arguments = match.group(2)
        return function_name, arguments
    else:
        return None, None
