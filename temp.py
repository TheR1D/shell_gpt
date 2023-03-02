.

import json
import os
import datetime

#returns a list of strings
birthday = json.loads(os.popen("python3 sgpt.py -r \"my birthday\" ").read())[0]
birthday_date = datetime.datetime.strptime(birthday, "%Y-%m-%d")
age = datetime.datetime.now().year - birthday_date.year

# create the file
file_name = "birthday.txt"
file_path = os.path.join(os.getcwd(), file_name)
with open(file_path, "w") as f:
    f.write(f"Happy Birthday! You are turning {age} today. Have a great day!")