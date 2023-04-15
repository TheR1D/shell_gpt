import platform
from os import getenv
from os.path import basename
import json
from distro import name as distro_name


"""
This module makes a prompt for OpenAI requests with some context.
Some of the following lines were inspired by similar open source project yolo-ai-cmdbot.
Credits: @demux79 @wunderwuzzi23
"""

# read in local json file as string
def read_json_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

STAC_COLLECTION = read_json_file(file_path="reference/stac/collection.json")
STAC_LANDSAT = read_json_file(file_path="reference/stac/landsat.json")
STAC_SENTINEL = read_json_file(file_path="reference/stac/sentinel.json")
RIO_SNIPPET = read_json_file(file_path="reference/rio/snippet.txt")
CLIENT_SNIPPET = read_json_file(file_path="reference/stac/client-snippet.txt")

SHELL_PROMPT = """
____

Here are some particular CLI packages to reccomend and their use cases:

stac-client
Important: when using stac-client DO NOT format bounding boxes like: --bbox 102.5,22.5,103.5,23.5
The correct format is: --bbox 102.5 22.5 103.5 23.5
Important: do not return a stac-client command without providing a URL. If the user does not specify, use https://landsatlook.usgs.gov/stac-server/
The cannonical stac-client command is: stac-client search URL --bbox BBOX --datetime DT --query QUERY
An example is: 
stac-client search https://landsatlook.usgs.gov/stac-server/  --bbox 102.5 22.5 103.5 23.5 --collections landsat-c2l2-sr --datetime 2022-09-01/2023-04-30 --query "eo:cloud_cover<20"
IMPORTANT: NO COMMAS IN BETWEEN NUMERIC BBOX VALUES. USE SPACES ONLY BETWEEN BBOX VALUES. NO EXECPTIONS.

____

"""

# stac
# # example stac items
# # the following are examples of json stac items. they do not follow actual catalog names or filenames, these must be queried from the 
# # catalogs or items specified by the user, most often using jq. for exampple, to get the band names in an item it's keys must be traversed.
# # the heirarchy represented in the examples below is a good guide for how to traverse the json responses.

# # COLLECTION EXAMPLE
# {STAC_COLLECTION}
# # LANDSAT EXAMPLE
# {STAC_LANDSAT}
# # SENTINEL EXAMPLE
# {STAC_SENTINEL}
# ____
# """.format(
#     STAC_COLLECTION=STAC_COLLECTION,
#     STAC_LANDSAT=STAC_LANDSAT,
#     STAC_SENTINEL=STAC_SENTINEL,
# )


# rio
# # rio is a command line tool for writing, reading, and manipulating geospatial raster data. it is the CLI for rasterio.
# # refer to rasterio docs for more details.
# {RIO_SNIPPET}

# Request: """


# open /Users/kevinlalli/.config/shell_gpt/roles/satgpt.json, set the 'role' value to SHELL_PROMPT
role_dict = json.loads(read_json_file(getenv("HOME") + "/.config/shell_gpt/roles/satgpt.json"))
role_dict["role"] += SHELL_PROMPT
with open(getenv("HOME") + "/.config/shell_gpt/roles/satgpt.json", "w") as f:
    f.write(json.dumps(role_dict))