# Shell GPT
A command-line interface (CLI) productivity tool for developers powered by OpenAI's GPT-3, will help you accomplish your tasks faster and more efficiently.

<div align="center">
    <img src="https://i.ibb.co/zVm2YYc/output-video-2.gif" width="800"/>
</div>

## Description
Chat GPT is a powerful language model developed by OpenAI that can generate human-like text. It can be used by us, coders, to generate code snippets, comments, documentation and more, helping us increase our productivity and efficiency while coding.

Forget about cheat sheets and notes, with this tool you can get accurate answers right in your terminal, and you'll probably find yourself reducing your daily Google searches, saving you valuable time and effort.

## Installation
```shell
pip install shell-gpt --user
```
On first start you would need to generate and provide your API key, get one [here](https://beta.openai.com/account/api-keys).

## Use cases
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
Usually we are forgetting commands like `chmod 444` and we want quickly find the answer in google, clicking pages, scrolling, copy&pasting, usually takes some time, but now we "google" and execute it right in the terminal using `--shell` flag `sgpt` will provide only shell commands:
```shell
# Here we are using special flag --shell, which will output only shell commands.
sgpt --shell "make all files in current directory read only"
# -> chmod 444 *
```
Since we are receiving valid shell command, we can execute it using `eval $(sgpt --shell "make all files in current directory read only")` but this is not very convenient, instead we can use `--execute` parameter:
```shell
sgpt --shell --execute "make all files in current directory read only"
# -> chmod 444 *
# -> Execute shell command? [y/N]: y
# ...
```
At this point it is already can solve half of my Google searches, but how far we can push the limits of Chat GPT? Let's try some docker containers:
```shell
sgpt --shell --execute "start nginx using docker, forward 443 and 80 port, mount current folder with index.html"
# -> docker run -d -p 443:443 -p 80:80 -v $(pwd):/usr/share/nginx/html nginx
# -> Execute shell command? [y/N]: y
# ...
```
Also, we can provide some parameters name in our prompt, for example, I want to pass input and output file names to ffmpeg:
```shell
sgpt --shell --execute "slow down video twice using ffmpeg, input video name \"input.mp4\" output video name \"output.mp4\""
# -> ffmpeg -i input.mp4 -filter:v "setpts=2.0*PTS" output.mp4
# -> Execute shell command? [y/N]: y
# ...
```
And remember we are in shell, this means we can use outputs of any commands in our prompt, this brings it to another level, here is simple examples with ffmpeg and list of videos in current folder:
```shell
ls
# -> 1.mp4 2.mp4 3.mp4
sgpt --shell --execute "using ffmpeg combine multiple videos into one without audio. Video file names $(ls)"
# -> ffmpeg -i 1.mp4 -i 2.mp4 -i 3.mp4 -filter_complex "[0:v] [1:v] [2:v] concat=n=3:v=1 [v]" -map "[v]" out.mp4
# -> Execute shell command? [y/N]: y
# ...
```
Since GPT-3 models can also do summarization and analyzing of input text, we can ask Chat GPT to find error in logs and provide some details:
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
Since it is valid python code without any other text, we can redirect the output to file:
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
--model                           TEXT     OpenAI model name. [default: text-davinci-003]
--max-tokens                      INTEGER  Strict length of output (words). [default: 2048]
--shell         --no-shell                 Get shell command as output. [default: no-shell]
--execute       --no-execute               Used with --shell, will execute command. [default: no-execute]
--code          --no-code                  Provide only code as output. [default: no-code]
--spinner       --no-spinner               Show loading spinner during API request. [default: spinner]
--animation     --no-animation             Typewriter animation. [default: animation]
--help                                     Show this message and exit.
```
