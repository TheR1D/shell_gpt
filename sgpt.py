"""
shell-gpt: An interface to OpenAI's GPT-3 API

This module provides a simple interface for OpenAI's GPT-3 API using Typer
as the command line interface. It supports different modes of output including
shell commands and code, and allows users to specify the desired OpenAI model
and length and other options of the output. Additionally, it supports executing
shell commands directly from the interface.

API Key is stored locally for easy use in future runs.
"""

import os
from enum import Enum
from time import sleep, gmtime, strftime
from pathlib import Path
from getpass import getpass
from types import DynamicClassAttribute
from tempfile import NamedTemporaryFile

import json
import typer
import requests
import yaml
import re

# Click is part of typer.
from click import MissingParameter, BadParameter, UsageError

from utils.terminal_functions import *
from utils.hugging_face import hugging_face_api
from utils.memory import filter_facts

# TODO: Add hugging face api call function and hugging face api key into config
# TODO: Merge so that alper has functions and new code structure
# TODO: Update naming of past programs/prompts
# Summarize the command below in 8 or fewer words.
# start nginx using docker, forward 443 and 80 port, mount current folder with index.html

API_URL = "https://api.openai.com/v1/completions"
DATA_FOLDER = os.path.expanduser("~/.config")
KEY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "config.yml"
FACT_MEMORY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "fact_memory.txt"

# pylint: disable=invalid-name
class Model(str, Enum):
    davinci = "text-davinci-003"
    curie = "text-curie-001"
    codex = "code-davinci-002"

    def __str__(self):
        return self.name

    @DynamicClassAttribute
    def value(self):
        return self.name


# pylint: enable=invalid-name
def create_config():
    openai_api_key = getpass(prompt="Please enter your OpenAI API secret key: ")
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(f"openai_api_key: {openai_api_key}\nhugging_face_naming: false")


def get_config(key):
    if not KEY_FILE.exists():
        create_config()
    with KEY_FILE.open(mode="r") as file:
        data = yaml.safe_load(file)
        try:
            return data[key]
        except KeyError:
            raise UsageError(
                f"Key '{key}' not found in config file. Please check your config file."
            )


def update_config(key, value):
    if not KEY_FILE.exists():
        create_config()

    with KEY_FILE.open(mode="r") as file:
        data = yaml.safe_load(file)

    data[key] = value

    with KEY_FILE.open(mode="w") as file:
        file.write(yaml.dump(data, default_flow_style=False))
    return value

def save_fact(fact):
    if not FACT_MEMORY_FILE.exists():
        FACT_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # write fact onto the file as a new line
    with open(FACT_MEMORY_FILE, "a") as file:
        file.write(fact + "\n")

def clear_fact_memory():
    if FACT_MEMORY_FILE.exists():
        FACT_MEMORY_FILE.unlink()



def get_edited_prompt():
    with NamedTemporaryFile(suffix=".txt", delete=False) as file:
        # Create file and store path.
        file_path = file.name
    editor = os.environ.get("EDITOR", "vim")
    # This will write text to file using $EDITOR.
    os.system(f"{editor} {file_path}")
    # Read file when editor is closed.
    with open(file_path, "r") as file:
        output = file.read()
    os.remove(file_path)
    if not output:
        raise BadParameter("Couldn't get valid PROMPT from $EDITOR")
    return output


@loading_spinner
def openai_request(prompt, model, max_tokens, api_key, temperature, top_p):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "prompt": prompt,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    response = requests.post(API_URL, headers=headers, json=data, timeout=180)
    response.raise_for_status()
    return response.json()["choices"][0]["text"]



# Using lambda to pass a function to default value, which make it apper as "dynamic" in help.

# cache should be able to be int or string
def main(
    prompt: str = typer.Argument(
        None, show_default=False, help="The prompt to generate completions for."
    ),
    model: Model = typer.Option("davinci", help="GPT-3 model name.", show_choices=True),
    max_tokens: int = typer.Option(
        lambda: 2048, help="Strict length of output (words)."
    ),
    temperature: float = typer.Option(
        lambda: 1.0, min=0.0, max=1.0, help="Randomness of generated output."
    ),
    top_probability: float = typer.Option(
        lambda: 1.0, min=0.1, max=1.0, help="Limits highest probable tokens."
    ),
    cache: bool = typer.Option(
        False, "--cache", "-c", help="Access the memory using name or an index."
    ),
    shell: bool = typer.Option(
        False, "--shell", "-s", help="Provide shell command as output."
    ),
    execute: bool = typer.Option(
        False, "--execute", "-e", help="Will execute --shell command."
    ),
    memorize_fact: bool = typer.Option(
        False,
        "--memorize",
        "-m",
        help="Will memorize the following fact you gave to ShellGPT.",
    ),
    clear_facts: bool = typer.Option(
        False, "--clear_facts", "-cf", help="Will clear facts you gave to ShellGPT."
    ),
    retrieve_fact: bool = typer.Option(
        False, "--retrieve", "-r", help="Will retrieve the desired fact."
    ),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
    set_history: int = typer.Option(
        lambda: 500, min=0, max=10000, help="Set the history length to be saved."
    ),  # TODO: Add this with naming
    set_openai_api_key: str = typer.Option(
        None, show_default=False, help="Set OpenAI API key."
    ),  # TODO: Add this with naming
    set_hugging_face_api_key: str = typer.Option(
        None, show_default=False, help="Set Hugging Face API key."
    ),  # TODO: Add this with naming
    toggle_hugging_face_naming: bool = typer.Option(
        False, show_default=False, help="Use or don't use hugging face naming."
    ),  # TODO: Add this with naming
    favorite: bool = typer.Option(
        False,
        help="Mark the command as a favorite command that can be searched through and won't be deleted.",
    ),  # TODO: Add this with naming
    ls_common: bool = typer.Option(
        False, help="List all common commands."
    ),  # TODO: Add this with naming using some model
    ls_history: bool = typer.Option(
        False, help="List all history."
    ),  # TODO: Add this with naming
):
    openai_api_key = get_config("openai_api_key")

    if clear_facts:
        clear_fact_memory()
        return

    if memorize_fact:
        curr_time = strftime("%H:%M:%S %d/%m/%Y", gmtime())
        save_fact(curr_time + " " + prompt)
        return

    if retrieve_fact:
        if not FACT_MEMORY_FILE.exists():
            typer.secho("No facts have been memorized yet.", fg="red")
            return
        else:
            query = prompt 
            hf_api_key = get_config("hugging_face_api_key")

            all_facts = FACT_MEMORY_FILE.read_text()
            filtered_facts = filter_facts(f"What is {query}?", all_facts, hf_api_key)

            fact_retrieval_prompt_path = "prompts/fact_retrieval_v1.txt"
            retrieval_prompt = Path(fact_retrieval_prompt_path).read_text()

            full_prompt = f"{retrieval_prompt}\n{filtered_facts}\n What is {query}?"

            response_text = openai_request(
                full_prompt,
                model,
                max_tokens,
                openai_api_key,
                0,
                top_probability,
                spinner=spinner,
            )
            response_text = response_text.strip()
            typer_writer(response_text, code, shell, animation)
        return

    if not prompt and not editor:
        if not set_history == 500:
            update_config("history_length", set_history)
            typer_writer(
                f"History length set to {set_history}.", False, False, animation
            )

        elif not set_openai_api_key == None:
            update_config("openai_api_key", set_openai_api_key)
            typer_writer(
                f"OpenAI API key set.", False, False, animation
            )

        elif not set_hugging_face_api_key == None:
            update_config("hugging_face_api_key", set_hugging_face_api_key)
            typer_writer(
                f"Hugging Face API key set.", False, False, animation
            )

        elif toggle_hugging_face_naming:
            if get_config("hugging_face_naming") == True:
                update_config("hugging_face_naming", False)
                typer_writer(
                    f"Hugging Face naming toggled to False.", False, False, animation
                )
            else:
                update_config("hugging_face_naming", True)
                typer_writer(
                    f"Hugging Face naming toggled to True.", False, False, animation
                )

        elif ls_common:
            pass

        elif ls_history:
            pass

        else:
            raise MissingParameter(param_hint="PROMPT", param_type="string")

        return 
    if cache:
        if prompt.isdigit():
            with open(".inst_memory.json", "r+") as jsonFile:
                data = json.load(jsonFile)
            N = len(data)
            if int(prompt) >= N:
                print("Index is out of range")
                return
            else:
                reversed_index = N - int(prompt) - 1
                output = data[reversed_index]["output"]
                typer_writer(output, code, shell, animation)
        else:
            print("need to implement lol")

        # modular as cache retrival function

        return

    if shell:
        # If default values where not changed, make it more accurate.
        if temperature == 1.0 == top_probability:
            temperature, top_probability = 0.2, 0.9
        prompt = f"{prompt}. Provide only shell command as output."
    elif code:
        # If default values where not changed, make it more creative (diverse).
        if temperature == 1.0 == top_probability:
            temperature, top_probability = 0.8, 0.2
        prompt = f"{prompt}. Provide only code as output."
    # Curie has hard cap 2048 + prompt.
    if model == "text-curie-001" and max_tokens == 2048:
        max_tokens = 1024
    if editor:
        prompt = get_edited_prompt()
    response_text = openai_request(
        prompt,
        model,
        max_tokens,
        openai_api_key,
        temperature,
        top_probability,
        spinner=spinner,
    )
    # For some reason OpenAI returns several leading/trailing white spaces.
    response_text = response_text.strip()
    typer_writer(response_text, code, shell, animation)

    if shell:
        if get_config("hugging_face_naming") == True:
            hugging_face_api_key = get_config("hugging_face_api_key")
            command_name = hugging_face_api("naming", {"inputs": "prompt", "max_length": 8, "min_length":3},  hugging_face_api_key)["summary_text"]
            # Make command_name lowercase and remove all special characters
            command_name = re.sub(r"[^a-zA-Z0-9]+", "", command_name).lower()
            print(command_name)
        else:
            pass # TODO: Implement naming
        write_to_memory(prompt, response_text, command_name, favorite)

    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(response_text)


def write_to_memory(input_text, output_text, name, favorite):
    dictionary = {
        "input": input_text,
        "output": output_text,
        "name": name,
        "favorite": favorite,
        "uid": False,
    }

    with open(".inst_memory.json", "r+") as jsonFile:
        data = json.load(jsonFile)

    data.append(dictionary)

    jsonFile = open(".inst_memory.json", "w+")
    jsonFile.write(json.dumps(data, indent=4))
    jsonFile.close()


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
