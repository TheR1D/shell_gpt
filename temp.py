import json
import os
import requests

#returns a list of strings
my_favorite_animal = json.loads(os.popen("python3 sgpt.py -r \"my favorite animal\" ").read())[0]
my_school_directory = json.loads(os.popen("python3 sgpt.py -r \"my school directory\" ").read())[0]

#download the wikipedia article
url = f"https://en.wikipedia.org/wiki/{my_favorite_animal}"
response = requests.get(url)

#write the article to a file
file_path = os.path.join(my_school_directory, f"{my_favorite_animal}.html")
with open(file_path, "w") as f:
    f.write(response.text)