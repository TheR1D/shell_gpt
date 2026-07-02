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

fish_integration = r"""
# Shell-GPT integration FISH v0.1
function _sgpt_fish
    if test -n "$(commandline)"
        set -g _sgpt_prev_cmd (commandline)
        commandline -r ""
        commandline -f repaint
        set -g _sgpt_result (sgpt --shell --no-interaction (echo "$_sgpt_prev_cmd"))
        commandline -r "$_sgpt_result"
        commandline -f end-of-line
    end
end
bind \cl _sgpt_fish
# Shell-GPT integration FISH v0.1
"""
