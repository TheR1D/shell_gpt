#!/bin/zsh
# Zsh is specified, but we'll try to make it somewhat portable or guide for Bash users.

# Script to interactively configure SGPT environment and config file

# --- Configuration ---
SGPT_CONFIG_FILE_DIR="$HOME/.config/shell_gpt"
SGPT_CONFIG_FILE="$SGPT_CONFIG_FILE_DIR/.sgptrc" # Common path

# --- OS and Shell Detection ---
OS_TYPE=$(uname -s)
CURRENT_SHELL_NAME=$(basename "$SHELL")
PREFERRED_SHELL_CONFIG_FILE=""
GCLOUD_SDK_INSTALL_URL="https://cloud.google.com/sdk/docs/install"
OPEN_URL_COMMAND=""

if [[ "$OS_TYPE" == "Darwin" ]]; then
    OPEN_URL_COMMAND="open"
    if [[ "$CURRENT_SHELL_NAME" == "zsh" ]]; then
        PREFERRED_SHELL_CONFIG_FILE="$HOME/.zshrc"
    elif [[ "$CURRENT_SHELL_NAME" == "bash" ]]; then
        PREFERRED_SHELL_CONFIG_FILE="$HOME/.bash_profile" # Or .bashrc
    else
        PREFERRED_SHELL_CONFIG_FILE="$HOME/.${CURRENT_SHELL_NAME}rc" # Generic guess
    fi
elif [[ "$OS_TYPE" == "Linux" ]]; then
    OPEN_URL_COMMAND="xdg-open"
    if [[ "$CURRENT_SHELL_NAME" == "zsh" ]]; then
        PREFERRED_SHELL_CONFIG_FILE="$HOME/.zshrc"
    elif [[ "$CURRENT_SHELL_NAME" == "bash" ]]; then
        PREFERRED_SHELL_CONFIG_FILE="$HOME/.bashrc"
    else
        PREFERRED_SHELL_CONFIG_FILE="$HOME/.${CURRENT_SHELL_NAME}rc" # Generic guess
    fi
else
    print_warning "Unsupported OS type: $OS_TYPE. Some features may not work as expected."
    PREFERRED_SHELL_CONFIG_FILE="$HOME/.profile" # A general fallback
    OPEN_URL_COMMAND="echo Please open this URL manually:"
fi


# --- Helper Functions ---
ask_yes_no() {
    local prompt="$1"
    local default_answer="${2:-n}"
    local answer

    while true; do
        if [[ "$default_answer" == "y" ]]; then
            read -r "answer?${prompt} [Y/n]: "
            answer="${answer:-y}"
        else
            read -r "answer?${prompt} [y/N]: "
            answer="${answer:-n}"
        fi

        case "$answer" in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) print -P "%F{yellow}Please answer yes (y) or no (n).%f";;
        esac
    done
}

print_info() { print -P "%F{cyan}$1%f"; }
print_success() { print -P "%F{green}$1%f"; }
print_warning() { print -P "%F{yellow}$1%f"; }
print_error() { print -P "%F{red}$1%f"; }

check_gcloud_installed() {
    if command -v gcloud &>/dev/null; then
        return 0
    else
        return 1
    fi
}

update_sgptrc_value() {
    local key="$1"
    local value="$2"
    local temp_file
    temp_file=$(mktemp)
    local found=false

    if [[ -f "$SGPT_CONFIG_FILE" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "#"*${key}*=* ]] || [[ "$line" == "${key}"*=* ]]; then
                print "${key}=${value}" >> "$temp_file"
                found=true
            else
                print "$line" >> "$temp_file"
            fi
        done < "$SGPT_CONFIG_FILE"
    fi

    if ! "$found"; then
        print "${key}=${value}" >> "$temp_file"
    fi
    mv "$temp_file" "$SGPT_CONFIG_FILE"
}

comment_out_sgptrc_key() {
    local key_to_comment="$1"
    local temp_file
    temp_file=$(mktemp)

    if [[ -f "$SGPT_CONFIG_FILE" ]]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "${key_to_comment}"*=* ]] && [[ "$line" != "#"* ]]; then
                print "#${line}" >> "$temp_file"
            else
                print "$line" >> "$temp_file"
            fi
        done < "$SGPT_CONFIG_FILE"
        mv "$temp_file" "$SGPT_CONFIG_FILE"
    fi
}

# --- gcloud Checks ---
GCLOUD_INSTALLED=false
if check_gcloud_installed; then
    GCLOUD_INSTALLED=true
    print_info "Google Cloud SDK (gcloud) is installed."
    if ask_yes_no "Would you like to check for updates to gcloud components now?"; then
        if gcloud components update; then
            print_success "gcloud components updated successfully (or are already up-to-date)."
        else
            print_warning "gcloud components update encountered an issue or was skipped by user."
        fi
    fi
else
    print_warning "Google Cloud SDK (gcloud) is NOT installed."
    print_warning "gcloud is required for proper Vertex AI (ADC) setup."

    if command -v curl &>/dev/null; then
        if ask_yes_no "Attempt to install gcloud SDK headlessly using Google's official script? (Installs to \$HOME/google-cloud-sdk)"; then
            print_info "Attempting headless installation of Google Cloud SDK..."
            print_info "This may take a few minutes. Please be patient."
            if curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir="$HOME/google-cloud-sdk"; then
                print_success "Google Cloud SDK installation script finished."
                print_warning "IMPORTANT: The gcloud SDK has been installed to '$HOME/google-cloud-sdk'."
                print_warning "You MUST add '$HOME/google-cloud-sdk/bin' to your PATH environment variable."
                print_warning "Typically, you would add the following line to your shell configuration file"
                print_warning "(e.g., '$PREFERRED_SHELL_CONFIG_FILE' for $CURRENT_SHELL_NAME users):"
                print_warning "  export PATH=\"\$HOME/google-cloud-sdk/bin:\$PATH\""
                print_warning "\nAfter adding it to your PATH, you need to source your shell configuration file"
                print_warning "(e.g., 'source $PREFERRED_SHELL_CONFIG_FILE') or open a new terminal session."
                print_warning "Once your PATH is updated, please RE-RUN THIS SCRIPT to continue with Vertex AI configuration."
            else
                print_error "Google Cloud SDK headless installation FAILED."
                print_info "Please try manual installation by visiting: $GCLOUD_SDK_INSTALL_URL"
            fi
        else
            print_info "Skipping automatic gcloud installation attempt."
            print_info "For manual installation, please visit: $GCLOUD_SDK_INSTALL_URL"
        fi
    else
        print_error "'curl' command not found. 'curl' is required for the headless gcloud installation attempt."
        print_info "Please install 'curl' first, or install gcloud manually by visiting: $GCLOUD_SDK_INSTALL_URL"
    fi
fi

# --- Main Script ---
print_info "\nSGPT Interactive Configuration Setup for $OS_TYPE (Shell: $CURRENT_SHELL_NAME)"
print_info "SGPT config file will be: $SGPT_CONFIG_FILE"
print_info "Shell startup file targeted for exports: $PREFERRED_SHELL_CONFIG_FILE"
print_info "--------------------------------------------------------------------"

mkdir -p "$SGPT_CONFIG_FILE_DIR"
if [[ -f "$SGPT_CONFIG_FILE" ]]; then
    cp "$SGPT_CONFIG_FILE" "${SGPT_CONFIG_FILE}.bak_$(date +%Y%m%d_%H%M%S)"
    print_info "Backed up existing $SGPT_CONFIG_FILE to ${SGPT_CONFIG_FILE}.bak_..."
fi

print_info "\nWhich API backend do you want to configure SGPT for?"
options=("OpenAI API Key" "Google AI Studio API Key (for Gemini)" "Google Vertex AI (ADC - Application Default Credentials)" "Exit")
select opt in "${options[@]}"; do
    REPLY_NUM=$REPLY # Store $REPLY as it might be overwritten by read
    case "$REPLY_NUM" in
        1) # OpenAI
            print_info "\nConfiguring for OpenAI..."
            read -r "api_key?Enter your OpenAI API Key (sk-...): "
            OPENAI_API_KEY_VAL="$api_key"
            [[ -z "$OPENAI_API_KEY_VAL" ]] && { print_error "API Key cannot be empty."; break; }


            read -r "default_model?Enter default OpenAI model (e.g., gpt-4o-mini, gpt-3.5-turbo) [gpt-4o-mini]: "
            DEFAULT_MODEL_VAL="${default_model:-gpt-4o-mini}"

            update_sgptrc_value "OPENAI_API_KEY" "\"$OPENAI_API_KEY_VAL\""
            comment_out_sgptrc_key "GOOGLE_API_KEY"
            comment_out_sgptrc_key "GOOGLE_CLOUD_PROJECT"
            comment_out_sgptrc_key "VERTEXAI_LOCATION"
            update_sgptrc_value "DEFAULT_MODEL" "$DEFAULT_MODEL_VAL"
            update_sgptrc_value "USE_LITELLM" "true"

            print_success "\nSGPT config file ($SGPT_CONFIG_FILE) updated for OpenAI."

            if ask_yes_no "Set OPENAI_API_KEY environment variable for the current session?"; then
                export OPENAI_API_KEY="$OPENAI_API_KEY_VAL"
                print_success "OPENAI_API_KEY set for current session."
            fi

            if [[ -n "$PREFERRED_SHELL_CONFIG_FILE" ]] && ask_yes_no "Add OPENAI_API_KEY to $PREFERRED_SHELL_CONFIG_FILE for future sessions?"; then
                print "\n# SGPT OpenAI Configuration (added by sgpt_setup.zsh)" >> "$PREFERRED_SHELL_CONFIG_FILE"
                print "export OPENAI_API_KEY=\"$OPENAI_API_KEY_VAL\"" >> "$PREFERRED_SHELL_CONFIG_FILE"
                print_success "OPENAI_API_KEY export added to $PREFERRED_SHELL_CONFIG_FILE."
                print_warning "Please run 'source $PREFERRED_SHELL_CONFIG_FILE' or open a new terminal to apply."
            fi
            break
            ;;
        2) # Google AI Studio
            print_info "\nConfiguring for Google AI Studio (Gemini API Key)..."
            read -r "api_key?Enter your Google AI Studio API Key (AIzaSy...): "
            GOOGLE_API_KEY_VAL="$api_key"
            [[ -z "$GOOGLE_API_KEY_VAL" ]] && { print_error "API Key cannot be empty."; break; }

            read -r "default_model?Enter default Gemini model (e.g., gemini/gemini-1.5-pro-latest) [gemini/gemini-1.5-pro-latest]: "
            DEFAULT_MODEL_VAL="${default_model:-gemini/gemini-1.5-pro-latest}"

            update_sgptrc_value "GOOGLE_API_KEY" "\"$GOOGLE_API_KEY_VAL\""
            comment_out_sgptrc_key "OPENAI_API_KEY"
            comment_out_sgptrc_key "GOOGLE_CLOUD_PROJECT"
            comment_out_sgptrc_key "VERTEXAI_LOCATION"
            update_sgptrc_value "DEFAULT_MODEL" "$DEFAULT_MODEL_VAL"
            update_sgptrc_value "USE_LITELLM" "true"

            print_success "\nSGPT config file ($SGPT_CONFIG_FILE) updated for Google AI Studio."

            if ask_yes_no "Set GOOGLE_API_KEY environment variable for the current session?"; then
                export GOOGLE_API_KEY="$GOOGLE_API_KEY_VAL"
                print_success "GOOGLE_API_KEY set for current session."
            fi

            if [[ -n "$PREFERRED_SHELL_CONFIG_FILE" ]] && ask_yes_no "Add GOOGLE_API_KEY to $PREFERRED_SHELL_CONFIG_FILE for future sessions?"; then
                print "\n# SGPT Google AI Studio Configuration (added by sgpt_setup.zsh)" >> "$PREFERRED_SHELL_CONFIG_FILE"
                print "export GOOGLE_API_KEY=\"$GOOGLE_API_KEY_VAL\"" >> "$PREFERRED_SHELL_CONFIG_FILE"
                print_success "GOOGLE_API_KEY export added to $PREFERRED_SHELL_CONFIG_FILE."
                print_warning "Please run 'source $PREFERRED_SHELL_CONFIG_FILE' or open a new terminal to apply."
            fi
            break
            ;;
        3) # Vertex AI (ADC)
            if ! "$GCLOUD_INSTALLED"; then
                print_error "Vertex AI setup requires Google Cloud SDK (gcloud) to be installed."
                print_error "Please install it first (this script may have offered to help if 'curl' is available),"
                print_error "update your PATH, and then re-run this script."
                break
            fi

            print_info "\nConfiguring for Google Vertex AI (Application Default Credentials)..."

            local current_gcloud_project
            current_gcloud_project=$(gcloud config get-value core/project 2>/dev/null)
            local project_prompt_text="Enter your Google Cloud Project ID"
            if [[ -n "$current_gcloud_project" ]]; then
                project_prompt_text+=" (current gcloud project: $current_gcloud_project)"
            fi
            project_prompt_text+=": "
            read -r "project_id?${project_prompt_text}"
            GOOGLE_CLOUD_PROJECT_VAL="${project_id:-$current_gcloud_project}"

            if [[ -z "$GOOGLE_CLOUD_PROJECT_VAL" ]]; then
                print_error "Google Cloud Project ID is required for Vertex AI setup. Aborting."
                break
            fi

            print_warning "\nFor Vertex AI ADC to work correctly with user credentials, ensure you have run:"
            print_warning "1. gcloud auth application-default login --project=$GOOGLE_CLOUD_PROJECT_VAL"
            print_warning "2. gcloud auth application-default set-quota-project $GOOGLE_CLOUD_PROJECT_VAL"
            print_info "This script cannot run these for you as they may require browser interaction."
            if ! ask_yes_no "Confirm you have ALREADY performed these two 'gcloud auth' steps for project '$GOOGLE_CLOUD_PROJECT_VAL'?" "y"; then
                print_error "Please run these gcloud commands in your terminal and then re-run this script option."
                print_warning "Aborting Vertex AI configuration."
                break
            fi

            read -r "location?Enter your Vertex AI Location (e.g., us-central1) [us-central1]: "
            VERTEXAI_LOCATION_VAL="${location:-us-central1}"

            read -r "default_model?Enter default Vertex AI model (e.g., vertex_ai/gemini-1.5-pro-001) [vertex_ai/gemini-1.5-pro-001]: "
            DEFAULT_MODEL_VAL="${default_model:-vertex_ai/gemini-1.5-pro-001}"

            comment_out_sgptrc_key "OPENAI_API_KEY"
            comment_out_sgptrc_key "GOOGLE_API_KEY"
            update_sgptrc_value "DEFAULT_MODEL" "$DEFAULT_MODEL_VAL"
            update_sgptrc_value "GOOGLE_CLOUD_PROJECT" "$GOOGLE_CLOUD_PROJECT_VAL"
            update_sgptrc_value "VERTEXAI_LOCATION" "$VERTEXAI_LOCATION_VAL"
            update_sgptrc_value "USE_LITELLM" "true"

            print_success "\nSGPT config file ($SGPT_CONFIG_FILE) updated for Vertex AI."
            print_info "Primary authentication will be via gcloud Application Default Credentials."
            print_info "Ensure GOOGLE_APPLICATION_CREDENTIALS env var is NOT set if using user ADC."

            local env_vars_to_set=()
            local env_vars_export_cmds=()
             if [[ -n "$GOOGLE_CLOUD_PROJECT_VAL" ]]; then
                env_vars_to_set+=("GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT_VAL")
                env_vars_export_cmds+=("export GOOGLE_CLOUD_PROJECT=\"$GOOGLE_CLOUD_PROJECT_VAL\"")
            fi
            if [[ -n "$VERTEXAI_LOCATION_VAL" ]]; then
                env_vars_to_set+=("VERTEXAI_LOCATION=$VERTEXAI_LOCATION_VAL")
                env_vars_export_cmds+=("export VERTEXAI_LOCATION=\"$VERTEXAI_LOCATION_VAL\"")
            fi

            if (( ${#env_vars_to_set[@]} > 0 )); then
                if ask_yes_no "Set GOOGLE_CLOUD_PROJECT & VERTEXAI_LOCATION env vars for the current session?"; then
                    for var_setting in "${env_vars_to_set[@]}"; do
                        eval "export $var_setting"
                    done
                    print_success "Vertex AI related environment variables set for current session."
                fi

                if [[ -n "$PREFERRED_SHELL_CONFIG_FILE" ]] && ask_yes_no "Add project/location environment variables to $PREFERRED_SHELL_CONFIG_FILE?"; then
                    print "\n# SGPT Vertex AI Configuration (added by sgpt_setup.zsh)" >> "$PREFERRED_SHELL_CONFIG_FILE"
                    for cmd_to_add in "${env_vars_export_cmds[@]}"; do
                        print "$cmd_to_add" >> "$PREFERRED_SHELL_CONFIG_FILE"
                    done
                    print "unset GOOGLE_API_KEY # Ensure Vertex AI ADC is used" >> "$PREFERRED_SHELL_CONFIG_FILE"
                    print "unset OPENAI_API_KEY # Ensure Vertex AI ADC is used" >> "$PREFERRED_SHELL_CONFIG_FILE"
                    print "# unset GOOGLE_APPLICATION_CREDENTIALS # Uncomment if you need to force user ADC over a service account file" >> "$PREFERRED_SHELL_CONFIG_FILE"
                    print_success "Vertex AI related exports added to $PREFERRED_SHELL_CONFIG_FILE."
                    print_warning "Please run 'source $PREFERRED_SHELL_CONFIG_FILE' or open a new terminal to apply."
                fi
            fi
            break
            ;;
        4) # Exit
            print_info "Exiting configuration."
            exit 0
            ;;
        *) print_warning "Invalid option ($REPLY_NUM). Please try again." ;;
    esac
done

print_info "\n--- Configuration Complete ---"
print_info "Next steps:"
print_info "1. If you updated a shell config file (e.g., $PREFERRED_SHELL_CONFIG_FILE), run 'source $PREFERRED_SHELL_CONFIG_FILE' or open a new terminal."
print_info "2. For Vertex AI, if you haven't already, complete the 'gcloud auth' steps in another terminal."
print_info "3. Test SGPT with a simple prompt: sgpt \"Hello world\""
print_info "   To use a specific model: sgpt --model <your_model_name> \"Hello world\""

exit 0