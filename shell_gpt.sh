# Default keybindings: zsh and bash have different syntax for keybindings.
declare -A KEYBINDINGS=(
    [toggle_zsh]='^@' # Control-Space
    [nl_execute_zsh]='[27;5;13~' # Control-Enter
    [toggle_bash]='\C-@'
    [nl_execute_bash]='[27;5;13~'
)

# Toggles the buffer between natural language and shell command, assuming
# it executes in zsh.
_sgpt_zsh() {
    # In zsh, the text in the terminal is stored in BUFFER.
    [[ -z $BUFFER ]] && BUFFER=$(fc -ln -1)

    # Cache the answers when toggling (optimization). If the keybinding
    # is pressed twice, then the first answer would already be stored.
    if [[ $BUFFER == $_sgpt_penult_cmd ]]; then
        # Swap the buffer and the previous cached result. Then store
        # the command that is being translated.
        tmp=$BUFFER
        BUFFER=$_sgpt_prev_cmd
        _sgpt_penult_cmd=$_sgpt_prev_cmd
        _sgpt_prev_cmd=$tmp
    else
        # If there is a mismatch (text changed between toggles), then the
        # result must be recalculated with sgpt.
        _sgpt_prev_cmd=$BUFFER
        BUFFER=$(_sgpt_translate_buffer "$BUFFER")
        _sgpt_penult_cmd=$BUFFER
    fi
    # Move cursor to end of line
    zle end-of-line
}

# Toggles the buffer between natural language and shell command, assuming
# it executes in bash.
_sgpt_bash() {
    # Small modification over _sgpt_zsh: use READLINE_LINE instead of BUFFER.
    # NOTE: These two functions could be merged using an indirect reference to the
    # buffer variable given as a parameter, but the method that is compatible with 
    # both zsh and bash is very messy: (https://tldp.org/LDP/abs/html/ivr.html)
    [[ -z $READLINE_LINE ]] && READLINE_LINE=$(fc -ln -1)

    if [[ $READLINE_LINE == $_sgpt_penult_cmd ]]; then
        tmp=$READLINE_LINE
        READLINE_LINE=$_sgpt_prev_cmd
        _sgpt_penult_cmd=$_sgpt_prev_cmd
        _sgpt_prev_cmd=$tmp
    else
        _sgpt_prev_cmd=$READLINE_LINE
        READLINE_LINE=$(_sgpt_translate_buffer "$READLINE_LINE")
        _sgpt_penult_cmd=$READLINE_LINE
    fi
    # Move cursor to end of line
    READLINE_POINT=${#READLINE_LINE}
}

# Decides whether the buffer contains shell command or natural language, then translates
# it to the other one using sgpt.
_sgpt_translate_buffer() {
    # The command name is the first word in the buffer
    local command_name=${1%% *}
    local sgpt_flag='--shell'

    # Decide if the buffer contains command or natural language.
    # If the first letter is lowercase and the command exists, then it is a command.
    if [[ ${1:0:1} = [[:lower:]] ]] && command -v $command_name > /dev/null; then
        sgpt_flag='--describe-shell'
    fi

    sgpt $sgpt_flag <<< $1
}

# Overrides the function that executes when a command is not found.
# First, decide if the incorrect command is natural language. If it is, 
# then translate to shell. If the translated command is destructive,
# then prompt before executing. Otherwise, directly execute.
command_not_found_handler() {
    # Determines if the command is actually just shell by two conditions:
    # 1. The first letter of the first word of the command is lowercased, and
    # 2. The number of words is below some arbitrary threshold, because natural
    #    language is much more verbose.
    local nl_word_count_threshold=6
    if [[ ${1:0:1} = [[:lower:]] && $(wc -w <<< "$@") -lt $nl_word_count_threshold ]]
    then
        # No need to translate, so return the exit code of the previous command
        echo "command not found: $@"
        return 1
    fi

    # Convert the natural language to shell
    local converted_command=$(sgpt --shell <<< "$@")

    # If it's destructive, then prompt for confirmation.
    if ! _sgpt_handle_destructive_command "$converted_command"; then
        return 1
    fi

    # Execute the translated command.
    # TODO Use subshell to execute command instead because it is safer then eval.
    eval "$converted_command"
}

# Same thing for bash, but slightly different function name
command_not_found_handle() { 
    command_not_found_handler "$@"
}

# Assume buffer is natural language. Translate and execute the command.
# First handle destructive commands, then execute the command, and add the
# natural language to history.
_sgpt_override_enter_zsh() {
    local converted_command=$(sgpt --shell <<< $BUFFER)
    zle -I
    if ! _sgpt_handle_destructive_command "$converted_command"; then
        BUFFER=''
        return 1
    fi

    # Execute the translated command, add the natural language 
    # to history, and clear the buffer
    eval "$converted_command"
    print -s "$BUFFER"
    BUFFER=''
}

# Same thing for bash, but no need to enable output or empty the buffer.
_sgpt_override_enter_bash() {
    local converted_command=$(sgpt --shell <<< $READLINE_LINE)
    if ! _sgpt_handle_destructive_command "$converted_command"; then
        return 1
    fi

    eval "$converted_command"
    history -s "$BUFFER"
    READLINE_LINE=''
}

# Prompts the user for confirmation if the command is destructive.
# If the command is not destructive or the user confirms, then return 0.
# Otherwise, return 1.
_sgpt_handle_destructive_command() {
    if _sgpt_is_destructive_command "$1"; then
        # Then prompt for confirmation
        echo "$1"
        echo "Execute destructive shell command? [y/N]:"
        read confirmation < /dev/tty
        # If user types enter or a word starting with n or N, then exit unsuccessfully
        if [[ -z $confirmation || ${confirmation:0:1} == [nN] ]]; then
            return 1
        fi
    fi
}

# Returns whether or not a given command mutates the system.
_sgpt_is_destructive_command() {
    # HACK: This is not an exhaustive way to check if the command
    # is destructive. There are flags in other common commands that
    # should be checked.
    local destructive_commands=(rm mv dd chmod sed git mkfs mkswap )
    local command_name=${1%% *}
    [[ "$destructive_commands[@]" =~ $command_name ]]
}

# Determine the type of shell, and execute the appropriate keybinding commmand
if [[ -n $ZSH_VERSION ]]; then
    zle -N _sgpt_zsh
    zle -N _sgpt_override_enter_zsh
    bindkey "${KEYBINDINGS[toggle_zsh]}" _sgpt_zsh
    bindkey "${KEYBINDINGS[nl_execute_zsh]}" _sgpt_override_enter_zsh
else
    bind -x "\"${KEYBINDINGS[toggle_bash]}\": _sgpt_bash"
    bind -x "\"${KEYBINDINGS[nl_execute_bash]}\": _sgpt_override_enter_bash"
fi
