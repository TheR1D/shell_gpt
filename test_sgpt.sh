test_is_destructive_command() {
    . ./shell_gpt.sh
    declare -A tests=(
        # 0 means destructive, 1 means safe
        ['git status']=1
        ['mv --no-clobber']=1
        ['rm -rf']=0
        ['ls -al']=1
        ['dd -f']=0
        ['sed -i']=0
    )
    for command in "${(k)tests[@]}"; do
        _sgpt_is_destructive_command "$command"
        [[ $? -eq ${tests[$command]} ]] || echo "Test failed for '$command'"
    done
}

test_handle_destructive_command() {
    . ./shell_gpt.sh
    echo "Instructions: Enter 'n' for rm, 'y' for dd, nothing for sed, and 'n' for find"
    declare -A tests=( 
        # 0 means handled, 1 means abort
        ['git status']=0
        ['mv --no-clobber x y']=0
        ['rm -rf folder']=1
        ['ls -al']=0
        ['dd if=~/a of=~/b']=0
        ['sed -i "s/foo/bar/g" file.txt']=1
        ['find . -type f -name "*.txt" -delete']=1
    )
    for command in "${(k)tests[@]}"; do
        _sgpt_handle_destructive_command "$command"
        [[ $? -eq ${tests[$command]} ]] || echo "Test failed for '$command'"
    done
}
