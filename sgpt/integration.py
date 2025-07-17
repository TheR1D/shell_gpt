bash_integration = """
# Shell-GPT integration BASH v0.2
_sgpt_bash() {
if [[ -n "$READLINE_LINE" ]]; then
    READLINE_LINE=$(sgpt --shell <<< "$READLINE_LINE" --no-interaction)
    READLINE_POINT=${#READLINE_LINE}
fi
}
bind -x '"\\C-l": _sgpt_bash'
# Shell-GPT integration BASH v0.2
"""

zsh_integration = """
# Shell-GPT integration ZSH v0.2
_sgpt_zsh() {
if [[ -n "$BUFFER" ]]; then
    _sgpt_prev_cmd=$BUFFER
    BUFFER+="⌛"
    zle -I && zle redisplay
    BUFFER=$(sgpt --shell <<< "$_sgpt_prev_cmd" --no-interaction)
    zle end-of-line
fi
}
zle -N _sgpt_zsh
bindkey ^l _sgpt_zsh
# Shell-GPT integration ZSH v0.2
"""

fish_integration = """
status is-interactive || exit

function _sgpt_commandline
    # Get the current command line content
    set -l _sgpt_prompt (commandline | string replace -r '^[ #]+' '')

    # Only proceed if there is a prompt
    if test -z "$_sgpt_prompt"
        return
    end

    # Append an hourglass to the current command
    commandline -a "⌛"
    commandline -f end-of-line  # needed to display the icon

    # Get the output of the sgpt command
    set -l _sgpt_output (echo "$_sgpt_prompt" | sgpt --shell --no-interaction)

    if test $status -eq 0
        # Replace the command line with the output from sgpt
        commandline -r -- (string trim "$_sgpt_output")
        commandline -a "  # $_sgpt_prompt"
    else
        # If the sgpt command failed, remove the hourglass
        commandline -f backward-delete-char
        commandline -a "  # ERROR: sgpt command failed"
    end
end

bind ctrl-o _sgpt_commandline
"""
