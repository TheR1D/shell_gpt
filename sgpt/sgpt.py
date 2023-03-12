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
from time import gmtime, strftime, time
from pathlib import Path
from types import DynamicClassAttribute

import json
import typer
import requests
import re

# Click is part of typer.
from click import MissingParameter

from terminal_functions import *
from hugging_face import hugging_face_api
from prompt_functions import *
from memory import *
from config import Config


API_URL = "https://api.openai.com/v1/completions"
DATA_FOLDER = os.path.expanduser("~/.sgpt")
CONFIG_FILE = Path(DATA_FOLDER) / "config.yml"
FACT_MEMORY_FILE = Path(DATA_FOLDER) / "fact_memory.txt"


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


# TODO: Move these config things to a config py file
# pylint: enable=invalid-name

# TODO: Move these to a memory file
def memorize_fact(fact):
    if not FACT_MEMORY_FILE.exists():
        FACT_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    # write fact onto the file as a new line
    with open(FACT_MEMORY_FILE, "a") as file:
        file.write(fact + "\n")


def clear_fact_memory():
    if FACT_MEMORY_FILE.exists():
        FACT_MEMORY_FILE.unlink()


def retrieve_fact(prompt, config):
    hf_api_key = config.get_config("hugging_face_api_key")

    all_facts = FACT_MEMORY_FILE.read_text()
    filtered_facts = filter_facts(f"What is {prompt}?", all_facts, filter="hf", hf_api_key=hf_api_key)

    fact_retrieval_prompt_path = "prompts/fact_retrieval_v1.txt"
    retrieval_prompt = Path(fact_retrieval_prompt_path).read_text()

    return f"{retrieval_prompt}\n{filtered_facts}\n What is {prompt}?"


# TODO: Move to util file
def save_to_history(input_text, output_text, name, favorite):
    dictionary = {
        "input": input_text,
        "output": output_text,
        "name": name,
        "favorite": favorite,
        "uid": round(time()*100),
    }

    with open(".inst_memory.json", "r+") as jsonFile:
        data = json.load(jsonFile)

    data.append(dictionary)

    jsonFile = open(".inst_memory.json", "w+")
    jsonFile.write(json.dumps(data, indent=4))
    jsonFile.close()


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
    ), # TODO: Should this be saved in the config?
    top_probability: float = typer.Option(
        lambda: 1.0, min=0.1, max=1.0, help="Limits highest probable tokens."
    ), # TODO: Should this be saved in the config?
    shell: bool = typer.Option(
        False, "--shell", "-s", help="Provide shell command as output."
    ),
    execute: bool = typer.Option(
        False, "--execute", "-e", help="Will execute --shell command."
    ),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),

    # === Newly added options below ===
    reset_config: bool = typer.Option(
        False, help="Resets the config file (WARNING: this will remove all your API keys)."
    ),
    set_history: int = typer.Option(
        lambda: 500, min=0, max=10000, help="Set the history size to be saved."
    ),
    set_openai_api_key: str = typer.Option(
        None, "--openai-key", help="Set OpenAI API key."
    ),
    set_hugging_face_api_key: str = typer.Option(
        None, "--hf-key", help="Set Hugging Face API key."
    ),
    toggle_hugging_face_naming: bool = typer.Option(
        False, "--hf-naming", help="Toggles using hugging face naming for commands in history."
    ),
    toggle_suggest_similar_prev_commands: bool = typer.Option(
        False, "--suggest-prev", help="Toggles searching through history to find similar commands before API call."
    ),

    memorize_fact: bool = typer.Option(
        False,
        "--memorize",
        "-m",
        help="Will memorize the following fact you gave to ShellGPT.",
    ),
    # TODO: How should we let users edit the fact memory? I feel like they should be able to easily edit the file in like nano or vim.
    clear_facts: bool = typer.Option(
        False, "--clear_facts", "-cf", help="Will all clear facts you gave to ShellGPT."
    ),
    retrieve_fact: bool = typer.Option(
        False, "--retrieve", "-r", help="Will retrieve the desired fact."
    ),
    # add_instruction: bool = typer.Option(
    #     False, "--add-instruction", "-ai", help="Will add instruction to ShellGPT."
    # ),
    # cache: bool = typer.Option(
    #     False, "--cache", "-c", help="Access the memory using name or an index."
    # ),
    favorite: bool = typer.Option(
        False, "--fav", "-f", help="Mark the command as a favorite command that won't be automatically deleted.",
    ),
    ls_fav: bool = typer.Option(
        False, "--lsf", help="List all favorite commands."
    ),
    ls_history: bool = typer.Option(
        False, "--lsh", help="List all history."
    ),
    ls_memory: bool = typer.Option(
        False, "--lsm", help="List all memory."
    )
):
    config = Config(CONFIG_FILE)

    openai_api_key = config.get_config("openai_api_key")

    # === Process config changes ===
    if reset_config:
        reset_config()

    elif not set_history == 500:
        config.update_config("history_length", set_history)
        typer_writer(
            f"History length set to {set_history}.", False, False, animation
        )

    elif not set_openai_api_key == None:
        config.update_config("openai_api_key", set_openai_api_key)
        typer_writer(f"OpenAI API key set.", False, False, animation)

    elif not set_hugging_face_api_key == None:
        config.update_config("hugging_face_api_key", set_hugging_face_api_key)
        typer_writer(f"Hugging Face API key set.", False, False, animation)

    elif toggle_hugging_face_naming:
        if config.get_config("hugging_face_naming") == True:
            config.update_config("hugging_face_naming", False)
            typer_writer(
                f"Hugging Face naming toggled to False.", False, False, animation
            )
        else:
            config.update_config("hugging_face_naming", True)
            typer_writer(
                f"Hugging Face naming toggled to True.", False, False, animation
            )
    elif toggle_suggest_similar_prev_commands:
        if config.get_config("suggest_similar_prev_commands") == True:
            config.update_config("suggest_similar_prev_commands", False)
            typer_writer(
                f"Suggesting similar previous commands before API call naming toggled to False.", False, False, animation
            )
        else:
            config.update_config("suggest_similar_prev_commands", True)
            typer_writer(
                f"Suggesting similar previous commands before API call naming toggled to True.", False, False, animation
            )

    # === Process memory ===
    if clear_facts:
        clear_fact_memory()
        return

    elif memorize_fact:
        curr_time = strftime("%H:%M:%S %d/%m/%Y", gmtime())
        memorize_fact(curr_time + " " + prompt)
        return

    elif retrieve_fact:
        if not FACT_MEMORY_FILE.exists():
            typer.secho("No facts have been memorized yet.", fg="red")
        else:
            request_prompt = retrieve_fact(prompt, config)
            
            # TODO: Move this to the bottom for everything
            # response_text = openai_request(
            #     full_prompt,
            #     model,
            #     max_tokens,
            #     openai_api_key,
            #     0,
            #     top_probability,
            #     spinner=spinner,
            # )
            # response_text = response_text.strip()
            # typer_writer(response_text, code, shell, animation)
        return
    
    # === Process ls* ===
    if ls_fav:
        # TODO: Implement
        pass

    elif ls_history:
        # TODO: Implement
        pass

    elif ls_memory:
        all_facts = FACT_MEMORY_FILE.read_text()
        print(all_facts)

    # === Process different prompts ===
    if favorite:
        typer.secho("Adding new instruction...", fg="green")
        instruction_prompt_path = "prompts/instruction_generation_v2.txt"

        instruction_prompt = Path(instruction_prompt_path).read_text()
        # custom_prompt = Path(prompt).read_text()

        request_prompt = instruction_prompt + " " + prompt

        # response_text = openai_request(
        #         full_prompt,
        #         model,
        #         max_tokens,
        #         openai_api_key,
        #         0,
        #         top_probability,
        #         spinner=spinner,
        #     )
        # response_text = response_text.strip()
        # typer_writer(response_text, code, shell, animation)

        # confirmation = input("Execute? (y/n)") # TODO: Fix this to not just be dumb input


        # #create a python file called temp.py and write the response_text to it
        # with open("temp.py", "w") as file:
        #     file.write(response_text)

        # if confirmation == "y":
        #     os.system("python temp.py")
        # else:
        #     typer.secho("Command not executed.", fg="red")

        return


    # TODO: Double check this if and other conditions to fail
    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")

    # if cache:
    #     if prompt.isdigit():
    #         with open(".inst_memory.json", "r+") as jsonFile:
    #             data = json.load(jsonFile)
    #         N = len(data)
    #         if int(prompt) >= N:
    #             print("Index is out of range")
    #             return
    #         else:
    #             reversed_index = N - int(prompt) - 1
    #             output = data[reversed_index]["output"]
    #             typer_writer(output, code, shell, animation)
    #     else:
    #         print("need to implement lol")

        # modular as cache retrival function

    if shell:
        # If default values where not changed, make it more accurate.
        if temperature == 1.0 == top_probability:
            temperature, top_probability = 0.2, 0.9
        request_prompt = f"{prompt}. Provide only shell command as output."
    elif code:
        # If default values where not changed, make it more creative (diverse).
        if temperature == 1.0 == top_probability:
            temperature, top_probability = 0.8, 0.2
        request_prompt = f"{prompt}. Provide only code as output."

    # === Call API ===
    # Curie has hard cap 2048 + prompt.
    if model == "text-curie-001" and max_tokens == 2048:
        max_tokens = 1024
    if editor:
        request_prompt = get_edited_prompt()
    response_text = openai_request(
        request_prompt,
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

    # === Name, save, and clean-up ===
    # if shell:
    if config.get_config("hugging_face_naming") == True:
        # TODO: Add spinning wheel
        hugging_face_api_key = config.get_config("hugging_face_api_key")
        command_name = hugging_face_api({"inputs": prompt, "parameters": {"max_length": 6, "min_length": 3}}, "naming", hugging_face_api_key, spinner=spinner)[0]["summary_text"]
        command_name = re.sub(r"[^a-zA-Z0-9]+", " ", command_name).lower().replace(" ", "_")

    else:
        prompt_list = re.sub(r"[^a-zA-Z0-9]+", " ", prompt).lower().split(" ")
        command_name = " ".join(prompt_list[:min(len(prompt_list), 4)])

    save_to_history(request_prompt, response_text, command_name, favorite)

    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(response_text)


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
