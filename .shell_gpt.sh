KEYBINDING='^s'

# Toggles the buffer between natural language and shell, assuming
# it executes in zsh.
_sgpt_zsh() {
    # The BUFFER variable contains the text
    [[ -z $BUFFER ]] && BUFFER=$(fc -ln -1)

    # Optimization: cache the results when toggling. If the keybinding
    # is pressed twice, then the first answer is already stored.
    if [[ $BUFFER == $_sgpt_penult_cmd ]]; then
        # Swap the buffer and the previous cached result. Then store
        # the command thats being translated
        tmp=$BUFFER
        BUFFER=$_sgpt_prev_cmd
        _sgpt_penult_cmd=$_sgpt_prev_cmd
        _sgpt_prev_cmd=$tmp
    else
        _sgpt_prev_cmd=$BUFFER
        BUFFER=$(_sgpt_translate_buffer "$BUFFER")
        _sgpt_penult_cmd=$BUFFER
    fi
}

# Toggles the buffer between natural language and shell, assuming
# it executes in bash.
_sgpt_bash() {
    # Small modification over _sgpt_zsh: use READLINE_BUFFER instead of BUFFER
    [[ -z $READLINE_BUFFER ]] && READLINE_BUFFER=$(fc -ln -1)

    if [[ $READLINE_BUFFER == $_sgpt_penult_cmd ]]; then
        tmp=$READLINE_BUFFER
        BUFFER=$_sgpt_prev_cmd
        _sgpt_penult_cmd=$_sgpt_prev_cmd
        _sgpt_prev_cmd=$tmp
    else
        _sgpt_prev_cmd=$READLINE_BUFFER
        READLINE_BUFFER=$(_sgpt_translate_buffer "$READLINE_BUFFER")
        _sgpt_penult_cmd=$READLINE_BUFFER
    fi
}

_sgpt_translate_buffer() {
    # The command name is the first word in the buffer
    local command_name=${1%% *}
    local sgpt_flag='--shell'

    # Decide if the buffer contains command or natural language
    if type $command_name > /dev/null; then
        sgpt_flag='--describe-shell'
    fi

    sgpt $sgpt_flag $1
}

# Overrides the function that executes when a command is not found
# Decides if the bad command is natural language. If it is, then translate
# to shell. If the translated command. If it is a destructive command, 
# prompt before executing. Otherwise, directly execute.
command_not_found_handler() {
    # If the command is shorter than 6 words, assume it is a regular shell command
    local nl_word_count_threshold=6
    if [[ $(echo $@ | wc -w) -lt $nl_word_count_threshold ]]; then 
        # Return the exit code of the previous command
        return $?
    fi

    # Convert the natural language to shell
    local converted_command=$(sgpt --shell "$@")

    # If it's destructive, then prompt for confirmation.
    if _sgpt_is_destructive_command $converted_command; then
        # Then prompt for confirmation
        echo "Execute shell command? [y/N]:"
        read confirmation
        # If confirmation starts with n or N, then exit unsuccessfully
        if [[ $confirmation == ^[Nn]* ]]; then
            return 1
        fi
    fi

    # Execute the translated command.
    # NOTE Using subshell to execute command is safer than eval
    $(echo $converted_command)
}

# Retusns whether or not a given commands makes an irreversable change
_sgpt_is_destructive_command() {
    # HACK: This is not an exhaustive way to check if the command
    # is destructive. There are flags in other common commands that
    # should be checked.
    local destructive_commands=(rm mv dd chmod mkfs mkswap )
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
