# ShellGPT
A command-line productivity tool powered by AI large language models (LLM). This command-line tool offers streamlined generation of **shell commands, code snippets, documentation**, eliminating the need for external resources (like Google search). Supports Linux, macOS, Windows and compatible with all major Shells like PowerShell, CMD, Bash, Zsh, etc.

https://github.com/smsmatt/shell_gpt/assets/16740832/9197283c-db6a-4b46-bfea-3eb776dd9093

## ⚠️ Important Notices & Warnings

**ShellGPT is experimental software. Use it at your own risk.**

*   **Potential System Modifications:** Features like shell command execution (`--shell`) and function calling can execute commands on your system. While designed to be helpful, there's a potential for unintended system modifications if the generated commands are incorrect or malicious, or if custom functions have side effects. Always review commands before execution, especially when using the interactive execution prompt.
*   **Data Privacy:** Do **NOT** use personally identifiable information (PII) or any sensitive data in your prompts when interacting with ShellGPT, especially when using third-party APIs like OpenAI or Vertex AI. Your prompts and generated responses may be processed and stored by these third-party services according to their terms of service and privacy policies.
*   **API Key Security:** Protect your API keys (e.g., OpenAI API key, Google Cloud credentials). Do not share them publicly or commit them to version control. ShellGPT stores API keys in its configuration file (`~/.config/shell_gpt/.sgptrc`). Ensure this file has appropriate permissions to restrict access. Consider using environment variables for API keys where possible, especially in shared or CI/CD environments, although ShellGPT primarily uses its config file.
*   **Experimental Features:** Some features, including interactions with newer models or less common LLM backends, might be more experimental than others.

By using ShellGPT, you acknowledge these risks.

## Installation

### General Requirements
*   **Python:** ShellGPT requires Python 3.10 or higher. You can check your Python version by running `python3 --version`.
*   **pip:** You'll need `pip` (Python's package installer) to install ShellGPT. It usually comes with Python. You can check if it's installed by running `pip3 --version`.

If you don't have Python or pip, please install them first according to your operating system's best practices.

### Installation Methods

Choose one of the following methods to install ShellGPT:

#### Method 1: Install from PyPI (Official Stable Release)

This method installs the latest stable version of the **original** ShellGPT from the Python Package Index (PyPI). This is recommended for most users who want a stable, official release.

1.  **Install ShellGPT:**
    Open your terminal and run:
    ```shell
    pip3 install shell-gpt
    ```
    *   If you encounter permission errors, you might need to use `pip3 install --user shell-gpt`. Ensure `~/.local/bin` (on Linux) is in your `PATH` if using `--user`.
    *   On some Linux distributions, you might need to install `python3-pip` first (e.g., `sudo apt install python3-pip` on Debian/Ubuntu).

2.  **Initial Setup (API Key & Configuration):**
    The first time you run `sgpt` (e.g., `sgpt "hello"`), if an API key is needed (e.g., for OpenAI), you will be prompted to enter it.
    For more comprehensive configuration, especially for backends like Google Vertex AI, ShellGPT might offer setup prompts or you may need to configure it manually (see "API Key and Backend Configuration" below). The interactive setup script (`sgpt_setup.zsh`) is primarily available when installing from the repository (Method 2).

#### Method 2: Install from Repository (Development/Forked Version)

This method is for users who want to install ShellGPT directly from a Git repository. This is useful for:
*   Installing a specific fork (like this one: `smsmatt/shell_gpt`).
*   Getting the very latest (potentially unstable) development code.
*   Contributing to development.

1.  **Clone the Repository:**
    Open your terminal and clone the desired repository. For this fork:
    ```shell
    git clone https://github.com/smsmatt/shell_gpt.git
    ```

2.  **Navigate to the Directory:**
    ```shell
    cd shell_gpt
    ```

3.  **Install ShellGPT and its Dependencies:**
    This command installs ShellGPT in your Python environment from the cloned source code.
    ```shell
    pip3 install .
    ```
    *   To install in editable mode (if you plan to modify the code and see changes immediately without reinstalling), you can use: `pip3 install -e .`

4.  **Initial Setup (API Key & Configuration using Setup Script):**
    After installation, the `sgpt` command will be available. The recommended way to configure ShellGPT, especially for backends like Google Vertex AI, is by using the interactive setup script:
    ```shell
    ./scripts/sgpt_setup.zsh
    ```
    This script will guide you through setting up API keys and other necessary configurations. It will create or update the configuration file at `~/.config/shell_gpt/.sgptrc`.

After installation via either method, proceed to the "API Key and Backend Configuration" section for details on setting up different LLM backends.
### API Key and Backend Configuration

ShellGPT supports various Large Language Model (LLM) backends. Configuration is primarily managed through the `~/.config/shell_gpt/.sgptrc` file.

**Recommended Setup Method (especially if installed from repository):**
If you installed ShellGPT from the repository (Method 2 above), the most straightforward way to configure backends is by running the interactive setup script:
```shell
./scripts/sgpt_setup.zsh
```
This script will guide you through setting up API keys and other necessary configurations for supported backends like OpenAI and Google Vertex AI.

If you installed via PyPI or prefer manual configuration, follow the instructions below.

#### 1. OpenAI (Default)

*   **Requirement:** An OpenAI API key.
*   **Setup:**
    1.  Generate an API key from [OpenAI Platform](https://platform.openai.com/account/api-keys).
    2.  When you first run `sgpt` (e.g., `sgpt "hello"`), you will be prompted to enter your API key.
    3.  Alternatively, the setup script (`./scripts/sgpt_setup.zsh`) will prompt for it.
    4.  The key will be stored in `~/.config/shell_gpt/.sgptrc`.
*   **Note:** OpenAI API usage is subject to their [pricing](https://openai.com/pricing).

#### 2. Google Vertex AI (for Gemini Models)

ShellGPT can use Gemini models through Google Cloud Vertex AI.

*   **Prerequisites:**
    1.  **Google Cloud Account:** You need an active Google Cloud Platform (GCP) account.
    2.  **GCP Project:** A GCP Project with billing enabled. Note your **Project ID**.
    3.  **Enable Vertex AI API:** In your GCP project, ensure the "Vertex AI API" is enabled. You can do this via the Google Cloud Console.
    4.  **Google Cloud SDK:** Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) on your machine.
    5.  **Authentication:** Authenticate the gcloud CLI with Application Default Credentials (ADC):
        ```shell
        gcloud auth application-default login
        ```
        This command will open a browser window for you to log in with your Google account that has access to the GCP project.

*   **Configuration with `sgpt_setup.zsh` (Recommended if installed from repository):**
    1.  Run the setup script: `./scripts/sgpt_setup.zsh`
    2.  The script will prompt you for your Google Cloud Project ID and the desired Vertex AI region (e.g., `us-central1`, `europe-west1`).
    3.  It will also help you select a default Gemini model (e.g., `gemini-1.5-pro-latest`).
    4.  These settings will be saved to `~/.config/shell_gpt/.sgptrc`.

*   **Manual Configuration (in `~/.config/shell_gpt/.sgptrc`):**
    If you are not using the setup script, add or modify the following lines in your `~/.config/shell_gpt/.sgptrc` file:
    ```ini
    # For Google Vertex AI
    GOOGLE_CLOUD_PROJECT=your-gcp-project-id
    VERTEXAI_LOCATION=your-gcp-region  # e.g., us-central1
    DEFAULT_MODEL=gemini-1.5-pro-latest # Or gemini-pro, gemini-1.0-pro, etc.
    # API_BASE_URL should typically be 'default' or left unset for Vertex AI,
    # as ShellGPT resolves the endpoint automatically.
    # API_BASE_URL=default
    ```
    Replace `your-gcp-project-id` and `your-gcp-region` with your actual project ID and preferred region.

#### 3. Google AI Studio (MakerSuite API Key for Gemini Models)

*   **Requirement:** An API Key from [Google AI Studio](https://aistudio.google.com/app/apikey).
*   **Configuration (in `~/.config/shell_gpt/.sgptrc`):**
    ```ini
    # For Google AI Studio (Gemini API via MakerSuite)
    API_BASE_URL=https://generativelanguage.googleapis.com # Or a specific versioned endpoint
    OPENAI_API_KEY=your_google_ai_studio_api_key # IMPORTANT: The config key is still OPENAI_API_KEY
    DEFAULT_MODEL=gemini-1.5-pro-latest # Or other compatible models like models/gemini-1.0-pro
    # Depending on your ShellGPT version and specific model, you might need USE_LITELLM=true
    # USE_LITELLM=true
    ```
    Replace `your_google_ai_studio_api_key` with your actual key.

#### 4. LiteLLM for Other Backends (including Local Models)

ShellGPT uses [LiteLLM](https://github.com/BerriAI/litellm) to support a wide range of LLM providers, including local models via backends like [Ollama](https://github.com/ollama/ollama).

*   **Setup:**
    1.  Ensure `litellm` is installed. If you installed `shell-gpt` from PyPI, you might need to install it as an extra: `pip3 install shell-gpt[litellm]`. If you installed from the repository using `pip3 install .`, `litellm` is now a core dependency.
    2.  Set `USE_LITELLM=true` in `~/.config/shell_gpt/.sgptrc`.
    3.  Configure `DEFAULT_MODEL` and `API_BASE_URL` according to LiteLLM's documentation for your chosen backend. For example, for Ollama running locally with a `mistral` model:
        ```ini
        USE_LITELLM=true
        DEFAULT_MODEL=ollama/mistral # Or your specific Ollama model
        API_BASE_URL=http://localhost:11434 # Default Ollama endpoint
        OPENAI_API_KEY=NA # LiteLLM might require a placeholder
        ```
    > [!TIP]
    > To use local models with Ollama, please follow this comprehensive [guide](https://github.com/smsmatt/shell_gpt/wiki/Ollama). (Note: Update this link if the wiki moves to the fork)
    >
    > **❗️Note that ShellGPT's performance and feature compatibility may vary with different backends and local models.**

---
**Overriding Models:**
You can always override the default model specified in the configuration file by using the `--model` flag with the `sgpt` command:
`sgpt --model gemini-1.5-pro-latest "Your prompt"`
---

## Usage
**ShellGPT** is designed to quickly analyse and retrieve information. It's useful for straightforward requests ranging from technical configurations to general knowledge.
```shell
sgpt "What is the fibonacci sequence"
# -> The Fibonacci sequence is a series of numbers where each number ...
```

ShellGPT accepts prompt from both stdin and command line argument. Whether you prefer piping input through the terminal or specifying it directly as arguments, `sgpt` got you covered. For example, you can easily generate a git commit message based on a diff:
```shell
git diff | sgpt "Generate git commit message, for my changes"
# -> Added main feature details into README.md
```

You can analyze logs from various sources by passing them using stdin, along with a prompt. For instance, we can use it to quickly analyze logs, identify errors and get suggestions for possible solutions:
```shell
docker logs -n 20 my_app | sgpt "check logs, find errors, provide possible solutions"
```
```text
Error Detected: Connection timeout at line 7.
Possible Solution: Check network connectivity and firewall settings.
Error Detected: Memory allocation failed at line 12.
Possible Solution: Consider increasing memory allocation or optimizing application memory usage.
```

You can also use all kind of redirection operators to pass input:
```shell
sgpt "summarise" < document.txt
# -> The document discusses the impact...
sgpt << EOF
What is the best way to lear Golang?
Provide simple hello world example.
EOF
# -> The best way to learn Golang...
sgpt <<< "What is the best way to learn shell redirects?"
# -> The best way to learn shell redirects is through...
```


### Shell commands
Have you ever found yourself forgetting common shell commands, such as `find`, and needing to look up the syntax online? With `--shell` or shortcut `-s` option, you can quickly generate and execute the commands you need right in the terminal.
```shell
sgpt --shell "find all json files in current folder"
# -> find . -type f -name "*.json"
# -> [E]xecute, [D]escribe, [A]bort: e
```

Shell GPT is aware of OS and `$SHELL` you are using, it will provide shell command for specific system you have. For instance, if you ask `sgpt` to update your system, it will return a command based on your OS. Here's an example using macOS:
```shell
sgpt -s "update my system"
# -> sudo softwareupdate -i -a
# -> [E]xecute, [D]escribe, [A]bort: e
```

The same prompt, when used on Ubuntu, will generate a different suggestion:
```shell
sgpt -s "update my system"
# -> sudo apt update && sudo apt upgrade -y
# -> [E]xecute, [D]escribe, [A]bort: e
```

Let's try it with Docker:
```shell
sgpt -s "start nginx container, mount ./index.html"
# -> docker run -d -p 80:80 -v $(pwd)/index.html:/usr/share/nginx/html/index.html nginx
# -> [E]xecute, [D]escribe, [A]bort: e
```

We can still use pipes to pass input to `sgpt` and generate shell commands:
```shell
sgpt -s "POST localhost with" < data.json
# -> curl -X POST -H "Content-Type: application/json" -d '{"a": 1, "b": 2}' http://localhost
# -> [E]xecute, [D]escribe, [A]bort: e
```

Applying additional shell magic in our prompt, in this example passing file names to `ffmpeg`:
```shell
ls
# -> 1.mp4 2.mp4 3.mp4
sgpt -s "ffmpeg combine $(ls -m) into one video file without audio."
# -> ffmpeg -i 1.mp4 -i 2.mp4 -i 3.mp4 -filter_complex "[0:v] [1:v] [2:v] concat=n=3:v=1 [v]" -map "[v]" out.mp4
# -> [E]xecute, [D]escribe, [A]bort: e
```

If you would like to pass generated shell command using pipe, you can use `--no-interaction` option. This will disable interactive mode and will print generated command to stdout. In this example we are using `pbcopy` to copy generated command to clipboard:
```shell
sgpt -s "find all json files in current folder" --no-interaction | pbcopy
```


### Shell integration
This is a **very handy feature**, which allows you to use `sgpt` shell completions directly in your terminal, without the need to type `sgpt` with prompt and arguments. Shell integration enables the use of ShellGPT with hotkeys in your terminal, supported by both Bash and ZSH shells. This feature puts `sgpt` completions directly into terminal buffer (input line), allowing for immediate editing of suggested commands.

https://github.com/smsmatt/shell_gpt/assets/16740832/bead0dab-0dd9-436d-88b7-6abfb2c556c1

To install shell integration, run `sgpt --install-integration` and restart your terminal to apply changes. This will add few lines to your `.bashrc` or `.zshrc` file. After that, you can use `Ctrl+l` (by default) to invoke ShellGPT. When you press `Ctrl+l` it will replace you current input line (buffer) with suggested command. You can then edit it and just press `Enter` to execute.

### Generating code
By using the `--code` or `-c` parameter, you can specifically request pure code output, for instance:
```shell
sgpt --code "solve fizz buzz problem using python"
```

```python
for i in range(1, 101):
    if i % 3 == 0 and i % 5 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
```
Since it is valid python code, we can redirect the output to a file:  
```shell
sgpt --code "solve classic fizz buzz problem using Python" > fizz_buzz.py
python fizz_buzz.py
# 1
# 2
# Fizz
# 4
# Buzz
# ...
```

We can also use pipes to pass input:
```shell
cat fizz_buzz.py | sgpt --code "Generate comments for each line of my code"
```
```python
# Loop through numbers 1 to 100
for i in range(1, 101):
    # Check if number is divisible by both 3 and 5
    if i % 3 == 0 and i % 5 == 0:
        # Print "FizzBuzz" if number is divisible by both 3 and 5
        print("FizzBuzz")
    # Check if number is divisible by 3
    elif i % 3 == 0:
        # Print "Fizz" if number is divisible by 3
        print("Fizz")
    # Check if number is divisible by 5
    elif i % 5 == 0:
        # Print "Buzz" if number is divisible by 5
        print("Buzz")
    # If number is not divisible by 3 or 5, print the number itself
    else:
        print(i)
```

### Chat Mode 
Often it is important to preserve and recall a conversation. `sgpt` creates conversational dialogue with each LLM completion requested. The dialogue can develop one-by-one (chat mode) or interactively, in a REPL loop (REPL mode). Both ways rely on the same underlying object, called a chat session. The session is located at the [configurable](#runtime-configuration-file) `CHAT_CACHE_PATH`.

To start a conversation, use the `--chat` option followed by a unique session name and a prompt.
```shell
sgpt --chat conversation_1 "please remember my favorite number: 4"
# -> I will remember that your favorite number is 4.
sgpt --chat conversation_1 "what would be my favorite number + 4?"
# -> Your favorite number is 4, so if we add 4 to it, the result would be 8.
```

You can use chat sessions to iteratively improve GPT suggestions by providing additional details.  It is possible to use `--code` or `--shell` options to initiate `--chat`:
```shell
sgpt --chat conversation_2 --code "make a request to localhost using python"
```
```python
import requests

response = requests.get('http://localhost')
print(response.text)
```

Let's ask LLM to add caching to our request:
```shell
sgpt --chat conversation_2 --code "add caching"
```
```python
import requests
from cachecontrol import CacheControl

sess = requests.session()
cached_sess = CacheControl(sess)

response = cached_sess.get('http://localhost')
print(response.text)
```

Same applies for shell commands:
```shell
sgpt --chat conversation_3 --shell "what is in current folder"
# -> ls
sgpt --chat conversation_3 "Sort by name"
# -> ls | sort
sgpt --chat conversation_3 "Concatenate them using FFMPEG"
# -> ffmpeg -i "concat:$(ls | sort | tr '\n' '|')" -codec copy output.mp4
sgpt --chat conversation_3 "Convert the resulting file into an MP3"
# -> ffmpeg -i output.mp4 -vn -acodec libmp3lame -ac 2 -ab 160k -ar 48000 final_output.mp3
```

To list all the sessions from either conversational mode, use the `--list-chats` or `-lc` option:  
```shell
sgpt --list-chats
# .../shell_gpt/chat_cache/conversation_1  
# .../shell_gpt/chat_cache/conversation_2
```

To show all the messages related to a specific conversation, use the `--show-chat` option followed by the session name:
```shell
sgpt --show-chat conversation_1
# user: please remember my favorite number: 4
# assistant: I will remember that your favorite number is 4.
# user: what would be my favorite number + 4?
# assistant: Your favorite number is 4, so if we add 4 to it, the result would be 8.
```

### REPL Mode  
There is very handy REPL (read–eval–print loop) mode, which allows you to interactively chat with GPT models. To start a chat session in REPL mode, use the `--repl` option followed by a unique session name. You can also use "temp" as a session name to start a temporary REPL session. Note that `--chat` and `--repl` are using same underlying object, so you can use `--chat` to start a chat session and then pick it up with `--repl` to continue the conversation in REPL mode.

<p align="center">
  <img src="https://s10.gifyu.com/images/repl-demo.gif" alt="gif">
</p>

```text
sgpt --repl temp
Entering REPL mode, press Ctrl+C to exit.
>>> What is REPL?
REPL stands for Read-Eval-Print Loop. It is a programming environment ...
>>> How can I use Python with REPL?
To use Python with REPL, you can simply open a terminal or command prompt ...
```

REPL mode can work with `--shell` and `--code` options, which makes it very handy for interactive shell commands and code generation:
```text
sgpt --repl temp --shell
Entering shell REPL mode, type [e] to execute commands or press Ctrl+C to exit.
>>> What is in current folder?
ls
>>> Show file sizes
ls -lh
>>> Sort them by file sizes
ls -lhS
>>> e (enter just e to execute commands, or d to describe them)
```

To provide multiline prompt use triple quotes `"""`:
```text
sgpt --repl temp
Entering REPL mode, press Ctrl+C to exit.
>>> """
... Explain following code:
... import random
... print(random.randint(1, 10))
... """
It is a Python script that uses the random module to generate and print a random integer.
```

You can also enter REPL mode with initial prompt by passing it as an argument or stdin or even both:
```shell
sgpt --repl temp < my_app.py
```
```text
Entering REPL mode, press Ctrl+C to exit.
──────────────────────────────────── Input ────────────────────────────────────
name = input("What is your name?")
print(f"Hello {name}")
───────────────────────────────────────────────────────────────────────────────
>>> What is this code about?
The snippet of code you've provided is written in Python. It prompts the user...
>>> Follow up questions...
```

### Function calling  
[Function calls](https://platform.openai.com/docs/guides/function-calling) is a powerful feature OpenAI provides. It allows LLM to execute functions in your system, which can be used to accomplish a variety of tasks. To install [default functions](https://github.com/smsmatt/shell_gpt/tree/main/sgpt/llm_functions/) run:
```shell
sgpt --install-functions
```

ShellGPT has a convenient way to define functions and use them. In order to create your custom function, navigate to `~/.config/shell_gpt/functions` and create a new .py file with the function name. Inside this file, you can define your function using the following syntax:
```python
# execute_shell_command.py
import subprocess
from pydantic import Field
from instructor import OpenAISchema


class Function(OpenAISchema):
    """
    Executes a shell command and returns the output (result).
    """
    shell_command: str = Field(..., example="ls -la", descriptions="Shell command to execute.")

    class Config:
        title = "execute_shell_command"

    @classmethod
    def execute(cls, shell_command: str) -> str:
        result = subprocess.run(shell_command.split(), capture_output=True, text=True)
        return f"Exit code: {result.returncode}, Output:\n{result.stdout}"
```

The docstring comment inside the class will be passed to OpenAI API as a description for the function, along with the `title` attribute and parameters descriptions. The `execute` function will be called if LLM decides to use your function. In this case we are allowing LLM to execute any Shell commands in our system. Since we are returning the output of the command, LLM will be able to analyze it and decide if it is a good fit for the prompt. Here is an example how the function might be executed by LLM:
```shell
sgpt "What are the files in /tmp folder?"
# -> @FunctionCall execute_shell_command(shell_command="ls /tmp")
# -> The /tmp folder contains the following files and directories:
# -> test.txt
# -> test.json
```

Note that if for some reason the function (execute_shell_command) will return an error, LLM might try to accomplish the task based on the output. Let's say we don't have installed `jq` in our system, and we ask LLM to parse JSON file:
```shell
sgpt "parse /tmp/test.json file using jq and return only email value"
# -> @FunctionCall execute_shell_command(shell_command="jq -r '.email' /tmp/test.json")
# -> It appears that jq is not installed on the system. Let me try to install it using brew.
# -> @FunctionCall execute_shell_command(shell_command="brew install jq")
# -> jq has been successfully installed. Let me try to parse the file again.
# -> @FunctionCall execute_shell_command(shell_command="jq -r '.email' /tmp/test.json")
# -> The email value in /tmp/test.json is johndoe@example.
```

It is also possible to chain multiple function calls in the prompt:
```shell
sgpt "Play music and open hacker news"
# -> @FunctionCall play_music()
# -> @FunctionCall open_url(url="https://news.ycombinator.com")
# -> Music is now playing, and Hacker News has been opened in your browser. Enjoy!
```

This is just a simple example of how you can use function calls. It is truly a powerful feature that can be used to accomplish a variety of complex tasks. We have dedicated [category](https://github.com/smsmatt/shell_gpt/discussions/categories/functions) in GitHub Discussions for sharing and discussing functions. 
LLM might execute destructive commands, so please use it at your own risk❗️

### Roles
ShellGPT allows you to create custom roles, which can be utilized to generate code, shell commands, or to fulfill your specific needs. To create a new role, use the `--create-role` option followed by the role name. You will be prompted to provide a description for the role, along with other details. This will create a JSON file in `~/.config/shell_gpt/roles` with the role name. Inside this directory, you can also edit default `sgpt` roles, such as **shell**, **code**, and **default**. Use the `--list-roles` option to list all available roles, and the `--show-role` option to display the details of a specific role. Here's an example of a custom role:
```shell
sgpt --create-role json_generator
# Enter role description: Provide only valid json as response.
sgpt --role json_generator "random: user, password, email, address"
```
```json
{
  "user": "JohnDoe",
  "password": "p@ssw0rd",
  "email": "johndoe@example.com",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345"
  }
}
```

If the description of the role contains the words "APPLY MARKDOWN" (case sensitive), then chats will be displayed using markdown formatting unless it is explicitly turned off with `--no-md`.

### Request cache
Control cache using `--cache` (default) and `--no-cache` options. This caching applies for all `sgpt` requests to OpenAI API:
```shell
sgpt "what are the colors of a rainbow"
# -> The colors of a rainbow are red, orange, yellow, green, blue, indigo, and violet.
```
Next time, same exact query will get results from local cache instantly. Note that `sgpt "what are the colors of a rainbow" --temperature 0.5` will make a new request, since we didn't provide `--temperature` (same applies to `--top-probability`) on previous request.

This is just some examples of what we can do using OpenAI GPT models, I'm sure you will find it useful for your specific use cases.

### Runtime configuration file
You can setup some parameters in runtime configuration file `~/.config/shell_gpt/.sgptrc`:
```text
# API key, also it is possible to define OPENAI_API_KEY env.
OPENAI_API_KEY=your_api_key
# Base URL of the backend server. If "default" URL will be resolved based on --model.
API_BASE_URL=default
# Max amount of cached message per chat session.
CHAT_CACHE_LENGTH=100
# Chat cache folder.
CHAT_CACHE_PATH=/tmp/shell_gpt/chat_cache
# Request cache length (amount).
CACHE_LENGTH=100
# Request cache folder.
CACHE_PATH=/tmp/shell_gpt/cache
# Request timeout in seconds.
REQUEST_TIMEOUT=60
# Default OpenAI model to use.
DEFAULT_MODEL=gpt-4o
# Default color for shell and code completions.
DEFAULT_COLOR=magenta
# When in --shell mode, default to "Y" for no input.
DEFAULT_EXECUTE_SHELL_CMD=false
# Disable streaming of responses
DISABLE_STREAMING=false
# The pygment theme to view markdown (default/describe role).
CODE_THEME=default
# Path to a directory with functions.
OPENAI_FUNCTIONS_PATH=/Users/user/.config/shell_gpt/functions
# Print output of functions when LLM uses them.
SHOW_FUNCTIONS_OUTPUT=false
# Allows LLM to use functions.
OPENAI_USE_FUNCTIONS=true
# Enforce LiteLLM usage (for local LLMs).
USE_LITELLM=false
```
Possible options for `DEFAULT_COLOR`: black, red, green, yellow, blue, magenta, cyan, white, bright_black, bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white.
Possible options for `CODE_THEME`: https://pygments.org/styles/

### Full list of arguments
```text
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────╮
│   prompt      [PROMPT]  The prompt to generate completions for.                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --model            TEXT                       Large language model to use. [default: gpt-4o]             │
│ --temperature      FLOAT RANGE [0.0<=x<=2.0]  Randomness of generated output. [default: 0.0]             │
│ --top-p            FLOAT RANGE [0.0<=x<=1.0]  Limits highest probable tokens (words). [default: 1.0]     │
│ --md             --no-md                      Prettify markdown output. [default: md]                    │
│ --editor                                      Open $EDITOR to provide a prompt. [default: no-editor]     │
│ --cache                                       Cache completion results. [default: cache]                 │
│ --version                                     Show version.                                              │
│ --help                                        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Assistance Options ─────────────────────────────────────────────────────────────────────────────────────╮
│ --shell           -s                      Generate and execute shell commands.                           │
│ --interaction         --no-interaction    Interactive mode for --shell option. [default: interaction]    │
│ --describe-shell  -d                      Describe a shell command.                                      │
│ --code            -c                      Generate only code.                                            │
│ --functions           --no-functions      Allow function calls. [default: functions]                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Chat Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --chat                 TEXT  Follow conversation with id, use "temp" for quick session. [default: None]  │
│ --repl                 TEXT  Start a REPL (Read–eval–print loop) session. [default: None]                │
│ --show-chat            TEXT  Show all messages from provided chat id. [default: None]                    │
│ --list-chats  -lc            List all existing chat ids.                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Role Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --role                  TEXT  System role for GPT model. [default: None]                                 │
│ --create-role           TEXT  Create role. [default: None]                                               │
│ --show-role             TEXT  Show role. [default: None]                                                 │
│ --list-roles   -lr            List roles.                                                                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Docker
Run the container using the `OPENAI_API_KEY` environment variable, and a docker volume to store cache. Consider to set the environment variables `OS_NAME` and `SHELL_NAME` according to your preferences.
```shell
docker run --rm \
           --env OPENAI_API_KEY=api_key \
           --env OS_NAME=$(uname -s) \
           --env SHELL_NAME=$(echo $SHELL) \
           --volume gpt-cache:/tmp/shell_gpt \
       ghcr.io/ther1d/shell_gpt -s "update my system"
```

Example of a conversation, using an alias and the `OPENAI_API_KEY` environment variable:
```shell
alias sgpt="docker run --rm --volume gpt-cache:/tmp/shell_gpt --env OPENAI_API_KEY --env OS_NAME=$(uname -s) --env SHELL_NAME=$(echo $SHELL) ghcr.io/ther1d/shell_gpt"
export OPENAI_API_KEY="your OPENAI API key"
sgpt --chat rainbow "what are the colors of a rainbow"
sgpt --chat rainbow "inverse the list of your last answer"
sgpt --chat rainbow "translate your last answer in french"
```

You also can use the provided `Dockerfile` to build your own image:
```shell
docker build -t sgpt .
```

### Docker + Ollama

If you want to send your requests to an Ollama instance and run ShellGPT inside a Docker container, you need to adjust the Dockerfile and build the container yourself: the litellm package is needed and env variables need to be set correctly.

Example Dockerfile:
```
FROM python:3-slim

ENV DEFAULT_MODEL=ollama/mistral:7b-instruct-v0.2-q4_K_M
ENV API_BASE_URL=http://10.10.10.10:11434
ENV USE_LITELLM=true
ENV OPENAI_API_KEY=bad_key
ENV SHELL_INTERACTION=false
ENV PRETTIFY_MARKDOWN=false
ENV OS_NAME="Arch Linux"
ENV SHELL_NAME=auto

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache /app[litellm] && mkdir -p /tmp/shell_gpt

VOLUME /tmp/shell_gpt

ENTRYPOINT ["sgpt"]
```


## Additional documentation
* [Azure integration](https://github.com/smsmatt/shell_gpt/wiki/Azure)
* [Ollama integration](https://github.com/smsmatt/shell_gpt/wiki/Ollama)
