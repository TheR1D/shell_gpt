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
        BUFFER="$BUFFER ⌛"
        zle redisplay
        BUFFER=$(_sgpt_translate_buffer "$_sgpt_prev_cmd" $1)
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
        READLINE_LINE=$(_sgpt_translate_buffer "$READLINE_LINE" $1)
        _sgpt_penult_cmd=$READLINE_LINE
    fi
    # Move cursor to end of line
    READLINE_POINT=${#READLINE_LINE}
}

_sgpt_toggle_nl_zsh() {
    _sgpt_zsh --toggle-nl
}

_sgpt_toggle_nl_bash() {
    _sgpt_bash --toggle-nl
}

# Decides whether the buffer contains shell command or natural language, then translates
# it to the other one using sgpt.
_sgpt_translate_buffer() {
    # The command name is the first word in the buffer
    local command_name=${1%% *}
    local sgpt_flag='--shell'

    # Decide if the buffer contains command or natural language.
    # If the first letter is lowercase and the command exists, then it is a command.
    if [[ -z $2 && ${1:0:1} = [[:lower:]] ]] && command -v $command_name > /dev/null; then
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
    printf '⌛'
    local converted_command=$(sgpt --shell <<< "$@")
    printf "\r"

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
    local old_buffer=$BUFFER
    BUFFER="$BUFFER ⌛"
    zle redisplay
    local converted_command=$(sgpt --shell <<< $old_buffer)
    BUFFER="$old_buffer"
    zle redisplay
    zle -I
    if ! _sgpt_handle_destructive_command "$converted_command"; then
        BUFFER=''
        return 1
    fi

    # Execute the translated command, add the natural language 
    # to history, and clear the buffer
    eval "$converted_command"
    print -s "$old_buffer"
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
    local config_options=(
        $(_sgpt_get_config_options SHELL_EXECUTE_NO_CONFIRM DEFAULT_EXECUTE_SHELL_CMD)
    )
    local confirm_string=$(
        [[ $config_options[2] == true ]] && echo 'Y/n' || echo 'y/N'
    )

    # If the command is destructive, then prompt for confirmation
    if _sgpt_is_destructive_command "$1"; then
        # Then prompt for confirmation
        echo -e "\033[1;31m${1}\033[0m" # Print the command in red
        echo -e "Execute \033[1mdestructive\033[0m shell command? [$confirm_string]:"
        read confirmation < /dev/tty
        # If user types enter or a word starting with n or N, then exit unsuccessfully
        if [[ ($config_options[2] != true \
            && -z $confirmation) || ${confirmation:0:1} == [nN] ]]; then
            return 1
        fi
    elif [[ $config_options[1] != true ]]; then
        # If the command is not destructive, then prompt for confirmation only if the
        # no-confirm configuration is not set to true.
        echo $1 # Print the command in green
        echo "Execute shell command? [$confirm_string]:"
        read confirmation < /dev/tty
        if [[ ($config_options[2] != true \
            && -z $confirmation) || ${confirmation:0:1} == [nN] ]]; then
            return 1
        fi
    fi
}

# Takes an array of config options and returns a space seperated
# string of their values. If a value is not set, then it is set to false.
_sgpt_get_config_options() {
    local config_options=""
    local config_path=~/.config/shell_gpt/.sgptrc

    [[ -f $config_path ]] && . $config_path

    for option in "$@"; do
        value=$(eval echo -E \$$option)
        [[ -z $value ]] && value='false'
        config_options+="$value "
    done
    echo -E $config_options
}

# Decides whether or not a given command mutates the system.
# Returns 0 if destructive, 1 if safe.
_sgpt_is_destructive_command() {
    local destructive_commands=(sudo rm mv cp dd chown chmod fdisk git modprobe mkfs mkswap)

    declare -A safe_flags_for_destructive_commands=(
        [rm]='-i --interactive --help --version'
        [mv]='-i --interactive -n --no-clobber --help --version'
        [cp]='-n --no-clobber --help --version'
        [git]='status log diff show fetch ls-files -h -v --help --version'
    )

    declare -A destructive_flags_for_safe_commands=(
        [sed]='-i --in-place'
        [find]='-delete'
    )

    local command_name=${1%% *}
   
    # If the command is destructive
    if [[ "$destructive_commands[@]" == *"$command_name"* ]]; then
        # If the command has a flag that makes it safe, then return 1
        for flag in $(echo $safe_flags_for_destructive_commands[$command_name]); do
            [[ "$1" == *"$flag"* ]] && return 1
        done
        return 0
    else
        for flag in $(echo $destructive_flags_for_safe_commands[$command_name]); do
            [[ "$1" == *"$flag"*  ]] && return 0
        done
        return 1
    fi
}

# Default keybindings
declare -A KEYBINDINGS=(
    [toggle_buffer]='\et' # Alt-t
    [execute_natural_language]='\ee' # Alt-e
    [toggle_natural_language]='\eT' # Alt-T
)

# Override default keybindings with user defined keybindings
config_keybindings=($(_sgpt_get_config_options TOGGLE_BUFFER_KEYBINDING \
    EXECUTE_NATURAL_LANGUAGE_KEYBINDING TOGGLE_NATURAL_LANGUAGE_KEYBINDING))
[[ $config_keybindings[1] != false ]] && KEYBINDINGS[toggle_buffer]=$config_keybindings[1]
[[ $config_keybindings[2] != false ]] && KEYBINDINGS[execute_natural_language]=$config_keybindings[2]
[[ $config_keybindings[3] != false ]] && KEYBINDINGS[toggle_natural_language]=$config_keybindings[3]

# Determine the type of shell, and execute the appropriate binding commmand
if [[ -n $ZSH_VERSION ]]; then
    zle -N _sgpt_zsh
    zle -N _sgpt_override_enter_zsh
    zle -N _sgpt_toggle_nl_zsh
    bindkey $KEYBINDINGS[toggle_buffer] _sgpt_zsh
    bindkey $KEYBINDINGS[execute_natural_language] _sgpt_override_enter_zsh
    bindkey $KEYBINDINGS[toggle_natural_language] _sgpt_toggle_nl_zsh
else
    bind -x "\"${KEYBINDINGS[toggle_buffer]}\": _sgpt_bash"
    bind -x "\"${KEYBINDINGS[execute_natural_language]}\": _sgpt_override_enter_bash"
    bind -x "\"${KEYBINDINGS[toggle_natural_language]}\": _sgpt_toggle_nl_bash"
fi
