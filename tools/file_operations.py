import os
import re


def read_prompt_from_file(filename):
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(script_dir, 'prompts', filename)
    with open(file_path, 'r') as file:
        return file.read().strip()


def clean_string(arg):
    return arg.strip().strip('"').strip("'")


def extract_function_calls(ai_response):
    """
    Extracts all function names and their single string arguments from a multi-line string,
    handling escaped single and double quotes within the arguments and recognizing code blocks.

    Args:
        ai_response (str): The AI response containing function calls, possibly within code blocks.

    Returns:
        list: A list of tuples, each containing the function name and its argument string.
              Returns an empty list if no function calls are found.
    """
    # Regular expression to match code blocks (e.g., ```sql ... ```)
    code_block_pattern = r"```(?:\w+)?\s*(.*?)```"
    code_blocks = re.findall(code_block_pattern, ai_response, re.DOTALL)

    # If no code blocks are found, consider the entire text
    if not code_blocks:
        code_blocks = [ai_response]

    function_calls = []

    # Regular expression to capture function calls with one string argument, handling escaped quotes
    function_pattern = r"""
        (\w+)                       # Function name: one or more word characters
        \s*\(                       # Opening parenthesis with optional whitespace
        \s*(['"])                   # Capture the opening quote (single or double)
        (                           # Start of argument capture group
            (?:\\.|[^\\\2])*        # Match escaped chars or non-quote/non-backslash characters
        )
        \2\s*                       # Match the corresponding closing quote
        \)                          # Closing parenthesis
    """

    regex = re.compile(function_pattern, re.VERBOSE | re.DOTALL)

    for block in code_blocks:
        for match in regex.finditer(block):
            function_name = match.group(1)
            argument = match.group(3)

            # Decode escaped characters within the argument string
            try:
                argument = bytes(argument, "utf-8").decode("unicode_escape")
            except UnicodeDecodeError:
                # If decoding fails, skip this match
                continue

            function_calls.append((function_name, argument))

    return function_calls
