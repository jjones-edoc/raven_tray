import os


def read_prompt_from_file(filename):
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(script_dir, 'prompts', filename)
    with open(file_path, 'r') as file:
        return file.read().strip()
