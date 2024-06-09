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
# Shell-GPT integration fish v0.1
function _sgpt_fish
    # Get the current command line content
    set -l _sgpt_prev_cmd (commandline)

    # Only proceed if there is a previous command
    if test -n "$_sgpt_prev_cmd"
        # Append an hourglass to the current command and repaint
        commandline -a "⌛"
        commandline -f repaint

        # Get the output of the sgpt command
        set -l _sgpt_output (echo "$_sgpt_prev_cmd" | sgpt --shell --no-interaction 2>/dev/null)

        # Check if the sgpt command was successful
        if test $status -eq 0
            # Replace the command line with the output from sgpt
            commandline -r -- (string trim "$_sgpt_output")
            commandline -f end-of-line
            commandline -f repaint
        else
            # If the sgpt command failed, remove the hourglass and display an error message
            commandline -f backward-delete-char
            commandline -f repaint
            echo "sgpt command failed. Please check your sgpt installation and configuration."
        end
    end
end

# Bind command search using sgpt to CTRL+/
bind \\c_ _sgpt_fish
# Shell-GPT integration fish v0.1
"""
