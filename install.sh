#!/bin/bash

# URLs of the shell scripts for ZSH and BASH
ZSH_SCRIPT_URL="https://raw.githubusercontent.com/TheR1D/shell_gpt/shell-integrations/simple_zsh.sh"
BASH_SCRIPT_URL="https://raw.githubusercontent.com/TheR1D/shell_gpt/shell-integrations/simple_bash.sh"

# Identify the shell
if [[ $SHELL =~ "zsh" ]]; then
  echo "Current shell is ZSH."
  SHELL_SCRIPT_URL=$ZSH_SCRIPT_URL
  PROFILE_FILE="$HOME/.zshrc"
elif [[ $SHELL =~ "bash" ]]; then
  echo "Current shell is BASH."
  SHELL_SCRIPT_URL=$BASH_SCRIPT_URL
  PROFILE_FILE="$HOME/.bashrc"
else
  echo "Your shell is not supported yet."
  echo "Current shell is neither ZSH nor BASH. Aborting."
  exit 1
fi

# Download the appropriate script
echo "Downloading shell script from $SHELL_SCRIPT_URL..."
echo "Appending the script to $PROFILE_FILE..."
curl -fsSL $SHELL_SCRIPT_URL >> ~/.zshrc

echo "Done."
