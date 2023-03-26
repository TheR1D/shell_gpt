import platform
from os import getenv, name as os_name
from os.path import basename, splitext
from distro import name as distro_name

SHELL_PROMPT = (
    "You are a assistant for programing on {os} and also you are expert in {shell}. "
    "All of you output must be a executable code string or really short answer. "
    "No explanation. No conclusion. No sorry. No excuses. No sudo. "
    "Do not show html, markdown, styled, colored formatting. "
    "just give the answer. "
)

CODE_PROMPT = (
    "You are a natural language to code translation engine. "
    "Do not show html, markdown, styled, colored formatting. "
    "Only the code is your output. "
    "Provide full solution. Make sure syntax is correct. "
    "Assume your output will be redirected to language specific file and executed. "
    "No explanation. No conclusion. "
)


def shell(question: str) -> dict:
    operating_systems = {
        "Linux": "Linux/" + distro_name(pretty=True),
        "Windows": "Windows " + platform.release(),
        "Darwin": "Darwin/MacOS " + platform.mac_ver()[0],
    }
    os = operating_systems.get(platform.system(), "Unknown")
    if os_name == 'nt':
        shell_type = splitext(basename(getenv('COMSPEC', 'Powershell')))[0]
    elif os_name == 'posix':
        shell_type = basename(getenv("SHELL", "bash"))
    else:
        shell_type = 'Unknown'
    question = question.strip()
    return dict(
        system=SHELL_PROMPT.format(shell=shell_type, os=os),
        user=question
    )


def code(question: str) -> dict:
    return dict(
        system=CODE_PROMPT,
        user=question
    )
