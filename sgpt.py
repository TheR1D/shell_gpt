import os
from time import sleep
from pathlib import Path

import typer
import requests

from utils import loading_spinner

API_URL = "https://api.openai.com/v1/completions"

app_data_folder = os.path.expanduser('~/.config')
api_key_file = Path(app_data_folder) / "shell-gpt" / "api_key.txt"


def get_api_key():
    if not api_key_file.exists():
        api_key = typer.prompt("Please enter your API secret key")
        api_key_file.parent.mkdir(parents=True, exist_ok=True)
        api_key_file.write_text(api_key)
    else:
        api_key = api_key_file.read_text()
    return api_key


@loading_spinner
def openai_request(prompt, model, max_tokens, api_key):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "prompt": prompt,
        "model": model,
        "max_tokens": max_tokens,
    }
    response = requests.post(API_URL, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["text"]


def typer_writer(text, code, shell, animate):
    shell_or_code = shell or code
    color = "magenta" if shell_or_code else None
    # typer.colors.
    if animate and not shell_or_code:
        for char in text:
            typer.secho(char, nl=False, fg=color, bold=shell_or_code)
            sleep(0.015)
        # Add new line at the end, to prevent % from appearing.
        typer.echo("")
        return
    typer.secho(text, fg=color, bold=shell_or_code)


def main(
    prompt: str,
    model: str = typer.Option("text-davinci-003", help="OpenAI model name."),
    max_tokens: int = typer.Option(2048, help="Strict length of output (words)."),
    shell: bool = typer.Option(False, "--shell", "-s", help="Provide shell command as output."),
    execute: bool = typer.Option(False, "--execute", "-e", help="Used with --shell, will execute command."),
    code: bool = typer.Option(False, help="Provide code as output."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
):
    api_key = get_api_key()
    if shell:
        prompt = f"{prompt}. Provide only shell command as output."
    elif code:
        prompt = f"{prompt}. Provide only code as output."
    response_text = openai_request(prompt, model, max_tokens, api_key, spinner=spinner)
    # For some reason OpenAI returns several leading/trailing white spaces.
    response_text = response_text.strip()
    typer_writer(response_text, code, shell, animation)
    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(response_text)


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
