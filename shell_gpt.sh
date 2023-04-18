KEYBINDING='\e ' # Default keybinding = Alt+Space

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
    # Small modification over _sgpt_zsh: use READLINE_BUFFER instead of BUFFER.
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

    # Decide if the buffer contains command or natural language
    if command -v $command_name > /dev/null; then
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
        return $?
    fi

    # Convert the natural language to shell
    local converted_command=$(sgpt --shell <<< "$@")

    # If it's destructive, then prompt for confirmation.
    if _sgpt_is_destructive_command "$converted_command"; then
        # Then prompt for confirmation
        echo "$converted_command"
        echo "Execute destructive shell command? [y/N]:"
        read confirmation
        # If user types enter or a word starting with n or N, then exit unsuccessfully
        if [[ -z $confirmation || ${confirmation:0:1} == [nN] ]]; then
            return 1
        fi
    fi

    # Execute the translated command.
    # TODO Use subshell to execute command instead because it is safer then eval.
    eval "$converted_command"
}

# Same thing for bash, but slightly different function name
command_not_found_handle() { 
    command_not_found_handler "$@"
}

# Retusns whether or not a given commands makes an irreversable change
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
    bindkey $KEYBINDING _sgpt_zsh
else
    bind -x "\"$KEYBINDING\": _sgpt_bash"
fi
