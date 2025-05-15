#!/bin/zsh
# Script to test and validate listing available Google-published Vertex AI models for a project and region.

# --- Helper Functions ---
print_info() { print -P "%F{cyan}INFO:%f $1"; }
print_success() { print -P "%F{green}SUCCESS:%f $1"; }
print_warning() { print -P "%F{yellow}WARNING:%f $1"; }
print_error() { print -P "%F{red}ERROR:%f $1"; }

print_info "Vertex AI Model Validation Script"
print_info "------------------------------------"

# --- Check for gcloud ---
if ! command -v gcloud &>/dev/null; then
    print_error "'gcloud' command not found in PATH. This script requires Google Cloud SDK."
    print_info "Please install it or ensure it's in your PATH."
    exit 1
fi
print_success "'gcloud' command found."

# --- Get User Input or Arguments ---
local gcp_project_id="$1"
local vertex_region="$2"
local quiet_mode=false

if [[ -n "$gcp_project_id" ]] && [[ -n "$vertex_region" ]]; then
    quiet_mode=true # Assume quiet mode if args are passed
else
    print_info "\nPlease provide your Google Cloud Project details."
    print_info "The gcloud command requires the ALPHANUMERIC Project ID (e.g., 'my-cool-project-123'), not the Project Number."
    read -r "gcp_project_id?Enter your Google Cloud Project ID (alphanumeric): "
    if [[ -z "$gcp_project_id" ]]; then
        print_error "Google Cloud Project ID cannot be empty."
        exit 1
    fi

    read -r "vertex_region?Enter your Vertex AI Region (e.g., us-central1): "
    if [[ -z "$vertex_region" ]]; then
        print_error "Vertex AI Region cannot be empty."
        exit 1
    fi
fi

if ! $quiet_mode; then
    print_info "\nAttempting to list Google-published models for Project ID '$gcp_project_id' in Region '$vertex_region'..."
fi

# --- Execute gcloud command ---
local gcloud_command
# Get full name and display name. We will filter for publisher client-side.
gcloud_command="gcloud ai models list --project=\"$gcp_project_id\" --region=\"$vertex_region\" --format=\"value(name,displayName)\""

if ! $quiet_mode; then
    print_info "Executing: $gcloud_command"
fi

local gcloud_output
local gcloud_exit_code

gcloud_output=$(eval $gcloud_command 2>&1)
gcloud_exit_code=$?

if ! $quiet_mode; then
    print_info "\n--- gcloud Command Output (Exit Code: $gcloud_exit_code) ---"
    print "$gcloud_output"
    print_info "--- End of gcloud Command Output ---"
fi

# --- Process Output ---
if [[ $gcloud_exit_code -eq 0 ]]; then
    local -a model_ids_to_output=() # For clean stdout in quiet mode

    if [[ "$gcloud_output" == *"listed 0 items"* ]]; then
        if ! $quiet_mode; then
            print_warning "\nSuccessfully queried, but gcloud listed 0 models for the specified project and region."
        fi
    elif [[ "$gcloud_output" == *"ERROR:"* ]] || \
         ( [[ "$gcloud_output" == *"WARNING:"* ]] && \
           [[ "$gcloud_output" != *"listed 0 items"* ]] && \
           [[ "$gcloud_output" != *"filter keys were not present"* ]] ) ; then
        if ! $quiet_mode; then
            print_warning "\ngcloud command executed but returned an error or significant warning in its output (see full output above)."
            if [[ "$gcloud_output" == *"You do not currently have an active account selected"* ]]; then
                print_error "GCLOUD AUTHENTICATION NEEDED: Please run 'gcloud auth login' in your terminal and then re-run this script."
            elif [[ "$gcloud_output" == *"set it to PROJECT ID instead"* ]]; then
                print_error "GCLOUD PROJECT ID ERROR: Ensure you entered the ALPHANUMERIC Project ID, not the project number."
            elif [[ "$gcloud_output" == *"not found or your project does not have access to it"* ]]; then
                print_error "ACCESS ERROR: The specified project may not exist, or you may not have permissions for Vertex AI, or the region might be incorrect."
            fi
        else
             print -u2 "Error or significant warning from gcloud: $gcloud_output"
        fi
    else # Potentially successful output with models, or only ignorable warnings
        if ! $quiet_mode; then
            print_success "\nSuccessfully fetched model list from gcloud (may include non-critical warnings)."
        fi
        local -a raw_model_lines=("${(@f)gcloud_output}") 
        local model_id_extracted

        if [[ ${#raw_model_lines[@]} -gt 0 ]]; then
            if ! $quiet_mode; then
                print_info "\nProcessed Model IDs (short names from Google-published models):"
            fi
            for line_data in "${raw_model_lines[@]}"; do
                # Skip empty lines or known informational lines from gcloud output
                if [[ -z "$line_data" ]] || [[ "$line_data" == "Using endpoint "* ]] || [[ "$line_data" == "Listed 0 items."* ]] || [[ "$line_data" == *"filter keys were not present"* ]]; then
                    continue
                fi
                
                local full_resource_name=$(echo "$line_data" | awk '{print $1}')
                
                if [[ -n "$full_resource_name" ]] && [[ "$full_resource_name" == "projects/"* ]]; then
                    if [[ "$full_resource_name" == *"/publishers/google/models/"* ]]; then
                        model_id_extracted=$(echo "$full_resource_name" | awk -F'/' '{print $NF}' | awk '{$1=$1};1') 
                        if [[ -n "$model_id_extracted" ]]; then
                            if [[ "$model_id_extracted" != *"ERROR:"* ]] && [[ "$model_id_extracted" != *"WARNING:"* ]]; then
                               model_ids_to_output+=("$model_id_extracted")
                               if ! $quiet_mode; then
                                   print "  - $model_id_extracted (from $full_resource_name)"
                               fi
                            elif ! $quiet_mode; then
                                print_info "DEBUG: Skipped potential model ID that looked like an error: $model_id_extracted (from $full_resource_name)"
                            fi
                        fi
                    fi
                elif ! $quiet_mode && [[ -n "$line_data" ]]; then 
                    print_info "DEBUG: Skipped unparseable line or non-project resource: $line_data"
                fi
            done
            
            if $quiet_mode && [[ ${#model_ids_to_output[@]} -gt 0 ]]; then
                printf "%s\n" "${model_ids_to_output[@]}" 
            elif [[ ${#model_ids_to_output[@]} -eq 0 ]] && ! $quiet_mode ; then
                 print_warning "Could not parse any Google-published model IDs from the gcloud output, or none were found that matched 'publishers/google'."
            fi
        elif ! $quiet_mode; then 
            print_warning "gcloud command returned no model data lines to parse."
        fi
    fi
else # gcloud command failed (exit code != 0)
    if ! $quiet_mode; then
        print_error "\ngcloud command failed with exit code $gcloud_exit_code (see full output above)."
        if [[ "$gcloud_output" == *"You do not currently have an active account selected"* ]]; then
            print_error "GCLOUD AUTHENTICATION NEEDED: Please run 'gcloud auth login' in your terminal and then re-run this script."
        elif [[ "$gcloud_output" == *"set it to PROJECT ID instead"* ]]; then
            print_error "GCLOUD PROJECT ID ERROR: Ensure you entered the ALPHANUMERIC Project ID, not the project number."
        fi
    else
        print -u2 "gcloud command failed (exit $gcloud_exit_code): $gcloud_output"
    fi
fi

if ! $quiet_mode; then
    print_info "\nValidation script finished."
fi
exit $gcloud_exit_code