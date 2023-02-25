#!/bin/bash

echo "This demo shows how to use the SGPT to create a student directory"
python3 sgpt.py --clear_facts
python3 sgpt.py -m "My school directory is /Users/alpercanberk/school"
python3 sgpt.py -m "This semester, I'm taking Modern Analysis, Complexity Theory, and Algos"
echo "1. Query my school directory from the memory 2. Create a file called notes.txt in the school directory 3. Query the memory for the classes that I'm taking, and write each class name in notes.txt file" > school_instructions.txt
python3 sgpt.py -ai school_instructions.txt
cat /Users/alpercanberk/school/notes.txt
