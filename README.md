# Shell GPT
A command-line productivity tool powered by OpenAI's GPT-3.5 model. As developers, we can leverage AI capabilities to generate shell commands, code snippets, comments, and documentation, among other things. Forget about cheat sheets and notes, with this tool you can get accurate answers right in your terminal, and you'll probably find yourself reducing your daily Google searches, saving you valuable time and effort.

<div align="center">
    <img src="https://i.ibb.co/nzPqnVd/sgpt-v0-8.gif" width="800"/>
</div>

## Installation
```shell
pip install shell-gpt==0.8.8
```
You'll need an OpenAI API key, you can generate one [here](https://beta.openai.com/account/api-keys).

If the`$OPENAI_API_KEY` environment variable is set it will be used, otherwise, you will be prompted for your key which will then be stored in `~/.config/shell_gpt/.sgptrc`.

## Usage
`sgpt` has a variety of use cases, including simple queries, shell queries, and code queries.
### Simple queries
We can use it as normal search engine, asking about anything:
```shell
sgpt "nginx default config file location"
# -> The default configuration file for Nginx is located at /etc/nginx/nginx.conf.
```
```shell
sgpt "mass of sun"
# -> = 1.99 × 10^30 kg
```
```shell
sgpt "1 hour and 30 minutes to seconds"
# -> 5,400 seconds
```
### Summarization and analyzing
ShellGPT accepts prompt from both stdin and command line argument, you choose the most convenient input method for your preferences. Whether you prefer piping input through the terminal or specifying it directly as arguments, `sgpt` got you covered. This versatile feature is particularly useful when you need to pass file content or pipe output from other commands to the GPT models for summarization or analysis. For example, you can easily generate a git commit message based on a diff:
```shell
git diff | sgpt "Generate git commit message, my changes"
# -> Commit message: Implement Model enum and get_edited_prompt()
```
You can analyze logs from various sources by passing them using stdin or command line arguments, along with a user-friendly prompt. This enables you to quickly identify errors and get suggestions for possible solutions:
```shell
docker logs -n 20 container_name | sgpt "check logs, find errors, provide possible solutions"
# ...
```
This powerful feature simplifies the process of managing and understanding data from different sources, making it easier for you to focus on what really matters: improving your projects and applications.

### Shell commands
Have you ever found yourself forgetting common shell commands, such as `chmod`, and needing to look up the syntax online? With `--shell` or shortcut `-s` option, you can quickly find and execute the commands you need right in the terminal.
```shell
sgpt --shell "make all files in current directory read only"
# -> chmod 444 *
# -> Execute shell command? [y/N]: y
# ...
```
Shell GPT is aware of OS and `$SHELL` you are using, it will provide shell command for specific system you have. For instance, if you ask `sgpt` to update your system, it will return a command based on your OS. Here's an example using macOS:
```shell
sgpt -s "update my system"
# -> sudo softwareupdate -i -a
```
The same prompt, when used on Ubuntu, will generate a different suggestion:
```shell
sgpt -s "update my system"
# -> sudo apt update && sudo apt upgrade -y
```
Let's try some docker containers:
```shell
sgpt -s "start nginx using docker, forward 443 and 80 port, mount current folder with index.html"
# -> docker run -d -p 443:443 -p 80:80 -v $(pwd):/usr/share/nginx/html nginx
# -> Execute shell command? [y/N]: y
# ...
```
We can still use pipes to pass input to `sgpt` and get shell commands as output:
```shell
cat data.json | sgpt -s "curl localhost with provided json"
# -> curl -X POST -H "Content-Type: application/json" -d '{"a": 1, "b": 2, "c": 3}' http://localhost
````
We can apply additional shell magic in our prompt, in this example passing file names to ffmpeg:
```shell
ls
# -> 1.mp4 2.mp4 3.mp4
sgpt -s "using ffmpeg combine multiple videos into one without audio. Video file names: $(ls -m)"
# -> ffmpeg -i 1.mp4 -i 2.mp4 -i 3.mp4 -filter_complex "[0:v] [1:v] [2:v] concat=n=3:v=1 [v]" -map "[v]" out.mp4
# -> Execute shell command? [y/N]: y
# ...
```
### Generating code
With `--code` parameters we can query only code as output, for example:
```shell
sgpt --code "Solve classic fizz buzz problem using Python"
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
Since it is valid python code, we can redirect the output to file:
```shell
sgpt --code "solve classic fizz buzz problem using Python" > fizz_buzz.py
python fizz_buzz.py
# 1
# 2
# Fizz
# 4
# Buzz
# Fizz
# ...
```
We can also use pipes to pass input to `sgpt`:
```shell
cat fizz_buzz.py | python -m sgpt --code "Generate comments for each line of my code"
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

### Chat
To start a chat session, use the `--chat` option followed by a unique session name and a prompt. You can also use "temp" as a session name to start a temporary chat session.
```shell
sgpt --chat number "please remember my favorite number: 4"
# -> I will remember that your favorite number is 4.
sgpt --chat number "what would be my favorite number + 4?"
# -> Your favorite number is 4, so if we add 4 to it, the result would be 8.
```
You can also use chat sessions to iteratively improve GPT suggestions by providing additional clues.
```shell
sgpt --chat python_requst --code "make an example request to localhost using Python"
```
```python
import requests

response = requests.get('http://localhost')
print(response.text)
```
Asking AI to add a cache to our request.
```shell
sgpt --chat python_request --code "add caching"
```
```python
import requests
from cachecontrol import CacheControl

sess = requests.session()
cached_sess = CacheControl(sess)

response = cached_sess.get('http://localhost')
print(response.text)
```
We can use `--code` or `--shell` options to initiate `--chat`, so you can keep refining the results:
```shell
sgpt --chat sh --shell "What are the files in this directory?"
# -> ls
sgpt --chat sh "Sort them by name"
# -> ls | sort
sgpt --chat sh "Concatenate them using FFMPEG"
# -> ffmpeg -i "concat:$(ls | sort | tr '\n' '|')" -codec copy output.mp4
sgpt --chat sh "Convert the resulting file into an MP3"
# -> ffmpeg -i output.mp4 -vn -acodec libmp3lame -ac 2 -ab 160k -ar 48000 final_output.mp3
```

### REPL
There is very handy REPL (read–eval–print loop) mode, which allows you to interactively chat with GPT models. To start a chat session in REPL mode, use the `--repl` option followed by a unique session name. You can also use "temp" as a session name to start a temporary REPL session. Note that `--chat` and `--repl` are using same chat sessions, so you can use `--chat` to start a chat session and then use `--repl` to continue the conversation in REPL mode. REPL mode will also show history of your conversation in the beginning.

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
>>> e (enter just e to execute commands)
...
```
Example of using REPL mode to generate code:
```text
sgpt --repl temp --code
Entering REPL mode, press Ctrl+C to exit.
>>> Using Python request localhost:80
import requests
response = requests.get('http://localhost:80')
print(response.text)
>>> Change port to 443
import requests
response = requests.get('https://localhost:443')
print(response.text)
```

### Chat sessions
To list all the current chat sessions, use the `--list-chat` option:
```shell
sgpt --list-chat
# .../shell_gpt/chat_cache/number
# .../shell_gpt/chat_cache/python_request
```
To show all the messages related to a specific chat session, use the `--show-chat` option followed by the session name:
```shell
sgpt --show-chat number
# user: please remember my favorite number: 4
# assistant: I will remember that your favorite number is 4.
# user: what would be my favorite number + 4?
# assistant: Your favorite number is 4, so if we add 4 to it, the result would be 8.
```

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
# OpenAI host, useful if you would like to use proxy.
OPENAI_API_HOST=https://api.openai.com
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
DEFAULT_MODEL=gpt-3.5-turbo
# Default color for OpenAI completions.
DEFAULT_COLOR=magenta
```
Possible options for `DEFAULT_COLOR`: black, red, green, yellow, blue, magenta, cyan, white, bright_black, bright_red, bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white.

### Full list of arguments
```text
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────╮
│   prompt      [PROMPT]  The prompt to generate completions for.                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --model            [gpt-3.5-turbo|gpt-4|gpt-4-32k]  OpenAI GPT model to use. [default: gpt-3.5-turbo]      │
│ --temperature      FLOAT RANGE [0.0<=x<=1.0]        Randomness of generated output. [default: 0.1]         │
│ --top-probability  FLOAT RANGE [0.1<=x<=1.0]        Limits highest probable tokens (words). [default: 1.0] │
│ --editor                                            Open $EDITOR to provide a prompt. [default: no-editor] │
│ --cache                                             Cache completion results. [default: cache]             │
│ --help                                              Show this message and exit.                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Assistance Options ───────────────────────────────────────────────────────────────────────────────────────╮
│ --shell  -s                 Generate and execute shell commands.                                           │
│ --code       --no-code      Generate only code. [default: no-code]                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Chat Options ─────────────────────────────────────────────────────────────────────────────────────────────╮
│ --chat        TEXT  Follow conversation with id, use "temp" for quick session. [default: None]             │
│ --repl        TEXT  Start a REPL (Read–eval–print loop) session. [default: None]                           │
│ --show-chat   TEXT  Show all messages from provided chat id. [default: None]                               │
│ --list-chat         List all existing chat ids. [default: no-list-chat]                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Docker
Run the container using the `OPENAI_API_KEY` environment variable, and a docker volume to store cache:
```shell
docker run --rm \
           --env OPENAI_API_KEY="your OPENAI API key" \
           --volume gpt-cache:/tmp/shell_gpt \
       ghcr.io/ther1d/shell_gpt --chat rainbow "what are the colors of a rainbow"
```

Example of a conversation, using an alias and the `OPENAI_API_KEY` environment variable:
```shell
alias sgpt="docker run --rm --env OPENAI_API_KEY --volume gpt-cache:/tmp/shell_gpt ghcr.io/ther1d/shell_gpt"
export OPENAI_API_KEY="your OPENAI API key"
sgpt --chat rainbow "what are the colors of a rainbow"
sgpt --chat rainbow "inverse the list of your last answer"
sgpt --chat rainbow "translate your last answer in french"
```

You also can use the provided `Dockerfile` to build your own image:
```shell
docker build -t sgpt .
```
