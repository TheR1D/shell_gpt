import json
import os
#returns a list of strings
my_research_directory = json.loads(os.popen("python3 sgpt.py -r 'my research directory'").read())[0]
execute_path = os.path.join(my_research_directory, 'main.py')
os.system(execute_path)