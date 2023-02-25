import json
import os
names = json.loads(os.popen("python3 sgpt.py -r 'in my research group'").read())
print(f"names={names}")
name_edu_dict = {}
for name in names:
    name_edu_dict[name] = json.loads(os.popen("python3 sgpt.py -r \"($name)'s level of education\"").read())[0]
for name in name_edu_dict.keys():
    print(f"{name}'s level of education is {name_edu_dict[name]}.")