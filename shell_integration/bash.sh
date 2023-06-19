# Shell-GPT integration BASH v0.2
_sgpt_bash() {
if [[ -n "$READLINE_LINE" ]]; then
	READLINE_LINE=$(sgpt --shell <<< "$READLINE_LINE")
    READLINE_POINT=${#READLINE_LINE}
fi
}
bind -x '"\C-l": _sgpt_bash'
# Shell-GPT integration BASH v0.2
