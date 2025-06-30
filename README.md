# ShellGPT
A command-line productivity tool powered by AI large language models (LLM). This command-line tool offers streamlined generation of **shell commands, code snippets, documentation**, eliminating the need for external resources (like Google search). Supports Linux, macOS, Windows and compatible with all major Shells like PowerShell, CMD, Bash, Zsh, etc.

https://github.com/TheR1D/shell_gpt/assets/16740832/9197283c-db6a-4b46-bfea-3eb776dd9093

## Installation
```shell
pip install shell-gpt
```
By default, ShellGPT uses OpenAI's API and GPT-4 model. You'll need an API key, you can generate one [here](https://beta.openai.com/account/api-keys). You will be prompted for your key which will then be stored in `~/.config/shell_gpt/.sgptrc`. OpenAI API is not free of charge, please refer to the [OpenAI pricing](https://openai.com/pricing) for more information.

### Azure OpenAI Provider
ShellGPT also supports Azure OpenAI provider. To use Azure OpenAI, you need to configure several Azure-specific parameters:

#### 1. Set the Provider
```shell
export OPENAI_PROVIDER=azure-openai
```

#### 2. Configure Azure Resource Endpoint
```shell
export AZURE_RESOURCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com
```

#### 3. Configure Deployment Name
```shell
export AZURE_DEPLOYMENT_NAME=your-deployment-name
```

#### 4. Set API Version
```shell
export API_VERSION=2025-01-01-preview
```

#### 5. Set API Key
```shell
export OPENAI_API_KEY=your_azure_openai_api_key
```

#### Configuration File
You can also set these in your configuration file `~/.config/shell_gpt/.sgptrc`:
```text
OPENAI_PROVIDER=azure-openai
AZURE_RESOURCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com
AZURE_DEPLOYMENT_NAME=your-deployment-name
API_VERSION=2025-01-01-preview
OPENAI_API_KEY=your_azure_openai_api_key
```

#### URL Structure
Azure OpenAI uses a different URL structure than standard OpenAI:
- **Standard OpenAI**: `https://api.openai.com/v1/chat/completions`
- **Azure OpenAI**: Uses the `AzureOpenAI` client which automatically constructs the correct URL format

The Azure OpenAI provider uses the official `AzureOpenAI` client from the OpenAI library, which handles the endpoint, deployment name, and API version automatically.

> [!TIP]
> Alternatively, you can use locally hosted open source models which are available for free. To use local models, you will need to run your own LLM backend server such as [Ollama](https://github.com/ollama/ollama). To set up ShellGPT with Ollama, please follow this comprehensive [guide](https://github.com/TheR1D/shell_gpt/wiki/Ollama).
>
> **❗️Note that ShellGPT is not optimized for local models and may not work as expected.**

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

https://github.com/TheR1D/shell_gpt/assets/16740832/bead0dab-0dd9-436d-88b7-6abfb2c556c1

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

To provide multiline prompt use triple quotes `