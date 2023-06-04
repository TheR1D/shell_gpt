# Shell-GPT integration BASH v0.1
_sgpt_bash() {
    READLINE_LINE=$(sgpt --shell <<< "$READLINE_LINE")
    READLINE_POINT=${#READLINE_LINE}
}
bind -x '^l' '_sgpt_bash'
# Shell-GPT integration BASH v0.1
