import os
import platform
import shutil
from pathlib import Path
from typing import Any

from ..config import cfg
from ..utils import option_callback

FUNCTIONS_FOLDER = Path(cfg.get("OPENAI_FUNCTIONS_PATH"))


@option_callback
def install_functions(*_args: Any) -> None:
    current_folder = os.path.dirname(os.path.abspath(__file__))
    common_folder = Path(current_folder + "/common")
    common_files = [Path(path) for path in common_folder.glob("*.py")]
    print("Installing default functions...")

    for file in common_files:
        print(f"Installed {FUNCTIONS_FOLDER}/{file.name}")
        shutil.copy(file, FUNCTIONS_FOLDER, follow_symlinks=True)

    current_platform = platform.system()
    if current_platform == "Linux":
        print("Installing Linux functions...")
    if current_platform == "Windows":
        print("Installing Windows functions...")
    if current_platform == "Darwin":
        print("Installing Mac functions...")
        mac_folder = Path(current_folder + "/mac")
        mac_files = [Path(path) for path in mac_folder.glob("*.py")]
        for file in mac_files:
            print(f"Installed {FUNCTIONS_FOLDER}/{file.name}")
            shutil.copy(file, FUNCTIONS_FOLDER, follow_symlinks=True)
