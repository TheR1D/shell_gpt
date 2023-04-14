import platform
from os import getenv, pathsep
from os.path import basename

from distro import name as distro_name

SHELL_PROMPT = """###
Provide only {shell} commands for {os} without any description.
If there is a lack of details, provide most logical solution.
Ensure the output is a valid shell command.
If multiple steps required try to combine them together.
Prompt: {prompt}
###
Command:"""

DESCRIBE_SHELL_PROMPT = """###
Provide an imperative, terse, single sentence description of the given shell command.
Do not repeat the given shell command or use any phrase indicating "this command".
Provide only plain text without Markdown formatting.
Command: du -cks
Answer: List the total disk usage of the current directory and its subdirectories in kilobytes.
Prompt: {prompt}
"""

CODE_PROMPT = """###
Provide only code as output without any description.
IMPORTANT: Provide only plain text without Markdown formatting.
IMPORTANT: Do not include markdown formatting such as ```.
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


def initial(prompt: str, shell: bool, describe_shell: bool, code: bool) -> str:
    # TODO: Can be prettified.
    prompt = prompt.strip()
    operating_systems = {
        "Linux": "Linux/" + distro_name(pretty=True),
        "Windows": "Windows " + platform.release(),
        "Darwin": "Darwin/MacOS " + platform.mac_ver()[0],
    }
    current_platform = platform.system()
    os_name = operating_systems.get(current_platform, current_platform)
    if current_platform in ("Windows", "nt"):
        is_powershell = len(getenv("PSModulePath", "").split(pathsep)) >= 3
        shell_name = "powershell.exe" if is_powershell else "cmd.exe"
    else:
        shell_name = basename(getenv("SHELL", "/bin/sh"))
    if shell:
        return SHELL_PROMPT.format(shell=shell_name, os=os_name, prompt=prompt)
    if describe_shell:
        return DESCRIBE_SHELL_PROMPT.format(prompt=prompt)
    if code:
        return CODE_PROMPT.format(prompt=prompt)
    return DEFAULT_PROMPT.format(shell=shell_name, os=os_name, prompt=prompt)
