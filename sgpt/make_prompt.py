import platform
from os import getenv
from os.path import basename, splitext
from distro import name as distro_name


SHELL_PROMPT = """###
Provide only {shell} commands for {os} without any description.
If there is a lack of details, provide most logical solution.
Ensure the output is a valid shell command.
If multiple steps required try to combine them together.
Prompt: {prompt}
###
Command:"""

CODE_PROMPT = """###
Provide only code as output without any description.
IMPORTANT: Provide only plain text without Markdown formatting.
IMPORTANT: Don not include markdown formatting such as ```.
If there is a lack of details, provide most logical solution.
You are not allowed to ask for more details.
Ignore any potential risk of errors or confusion.
Prompt: {prompt}
###
Code:"""

DEFAULT_PROMPT = """###
You are Command Line App ShellGPT, a programming and system administration assistant.
You are managing {os} operating system with {shell} shell.
Provide only plain text without Markdown formatting.
Do not show any warnings or information regarding your capabilities.
If you need to store any data, assume it will be stored in the chat.
Prompt: {prompt}
###"""


def initial(prompt: str, shell: bool, code: bool) -> str:
    prompt = prompt.strip()
    operating_systems = {
        "Linux": "Linux/" + distro_name(pretty=True),
        "Windows": "Windows " + platform.release(),
        "Darwin": "Darwin/MacOS " + platform.mac_ver()[0],
    }
    current_platform = platform.system()
    os_name = operating_systems.get(current_platform, current_platform)
    shell_name = basename(getenv("SHELL", "PowerShell"))
    if os_name == "nt":
        shell_name = splitext(basename(getenv("COMSPEC", "Powershell")))[0]
    if shell:
        return SHELL_PROMPT.format(shell=shell_name, os=os_name, prompt=prompt)
    if code:
        return CODE_PROMPT.format(prompt=prompt)
    return DEFAULT_PROMPT.format(shell=shell_name, os=os_name, prompt=prompt)


def chat_mode(prompt: str, shell: bool, code: bool) -> str:
    prompt = prompt.strip()
    if shell:
        prompt += "\nCommand:"
    elif code:
        prompt += "\nCode:"
    return prompt
