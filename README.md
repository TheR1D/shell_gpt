# Shell GPT
A command-line interface (CLI) productivity tool powered by OpenAI's Davinci model, that will help you accomplish your tasks faster and more efficiently.

<div align="center">
    <img src="https://i.ibb.co/QX236hx/sgpt-5-0-0.gif" width="800"/>
</div>

## Description
`text-davinci-003` is a powerful language model developed by OpenAI that can generate human-like text. It can be used by us developers, to generate code snippets, comments, documentation and more, helping us increase our productivity and efficiency while coding.

Forget about cheat sheets and notes, with this tool you can get accurate answers right in your terminal, and you'll probably find yourself reducing your daily Google searches, saving you valuable time and effort.

## Installation
```shell
pip install shell-gpt --user
```
On first start you would need to generate and provide your API key, get one [here](https://beta.openai.com/account/api-keys).

## Usage
`sgpt` has a variety of use cases, including simple queries, shell queries, and code queries.
### Simple queries
We can use it pretty much as normal search engine, asking about anything, for example:
```shell
sgpt "nginx default config file location"
# -> The default Nginx config location is /etc/nginx/nginx.conf
sgpt "docker show all local images"
# -> You can view all locally available Docker images by running: `docker images`
sgpt "mass of sun"
# -> = 1.99 × 10^30 kg
```
### Shell queries
Usually we are forgetting commands like `chmod 444` and we want quickly find the answer in google, but now we "google" and execute it right in the terminal using `--shell` flag `sgpt` will provide only shell commands:
```shell
sgpt --shell "make all files in current directory read only"
# -> chmod 444 *
```
Since we are receiving valid shell command, we can execute it using `eval $(sgpt --shell "make all files in current directory read only")` but this is not very convenient, instead we can use `--execute` (or shortcut `-se` for `--shell` `--execute`) parameter:
```shell
sgpt --shell --execute "make all files in current directory read only"
# -> chmod 444 *
# -> Execute shell command? [y/N]: y
# ...
```
Let's try some docker containers:
```shell
sgpt -se "start nginx using docker, forward 443 and 80 port, mount current folder with index.html"
# -> docker run -d -p 443:443 -p 80:80 -v $(pwd):/usr/share/nginx/html nginx
# -> Execute shell command? [y/N]: y
# ...
```
Also, we can provide some parameters name in our prompt, for example, passing output file name to ffmpeg:
```shell
sgpt -se "slow down video twice using ffmpeg, input video name \"input.mp4\" output video name \"output.mp4\""
# -> ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS" output.mp4
# -> Execute shell command? [y/N]: y
# ...
```
We can apply additional shell magic in our prompt, in this example passing file names to ffmpeg:
```shell
ls
# -> 1.mp4 2.mp4 3.mp4
sgpt -se "using ffmpeg combine multiple videos into one without audio. Video file names: $(ls -m)"
# -> ffmpeg -i 1.mp4 -i 2.mp4 -i 3.mp4 -filter_complex "[0:v] [1:v] [2:v] concat=n=3:v=1 [v]" -map "[v]" out.mp4
# -> Execute shell command? [y/N]: y
# ...
```
Since GPT-3 models can also do summarization and analyzing of input text, we can ask `text-davinci-003` to generate commit message:
```shell
sgpt "Generate git commit message with details, my changes: $(git diff)"
# -> Commit message: Implement Model enum and get_edited_prompt() func, add temperature, top_p and editor args for OpenAI request.
```
Or ask it to find error in logs and provide more details:
```shell
sgpt "check these logs, find errors, and explain what the error is about: ${docker logs -n 20 container_name}"
# ...
```
### Code queries
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
This is, just some examples of what we can do using GPT-3 models, I'm sure you will find it useful for your specific use cases.

### Full list of arguments
```shell
╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   prompt      [PROMPT]  The prompt to generate completions for.                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --model                                  [davinci|curie|codex]      GPT-3 model name. [default: davinci]                        │
│ --max-tokens                             INTEGER                    Strict length of output (words). [default: (dynamic)]       │
│ --temperature                            FLOAT RANGE [0.0<=x<=1.0]  Randomness of generated output. [default: (dynamic)]        │
│ --top-probability                        FLOAT RANGE [0.1<=x<=1.0]  Limits highest probable tokens. [default: (dynamic)]        │
│ --shell            -s                                               Provide shell command as output.                            │
│ --execute          -e                                               Will execute --shell command.                               │
│ --code                 --no-code                                    Provide code as output. [default: no-code]                  │
│ --editor               --no-editor                                  Open $EDITOR to provide a prompt. [default: no-editor]      │
│ --animation            --no-animation                               Typewriter animation. [default: animation]                  │
│ --spinner              --no-spinner                                 Show loading spinner during API request. [default: spinner] │
│ --help                                                              Show this message and exit.                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Docker
Use the provided `Dockerfile` to build a container:
```shell
docker build -t sgpt .
```

You may use a named volume (therefore sgpt will ask your API key only once) to run the container:
```shell
docker run --rm -ti -v gpt-config:/home/app/.config/shell-gpt sgpt "what are the colors of a rainbow"
```

