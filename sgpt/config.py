import yaml
from getpass import getpass
from click import UsageError

class Config:
    DEFAULT_CONFIG = "hugging_face_naming: false\nhistory_length: 500"

    def __init__(self, config_file):
        self.config_file = config_file


    def create_config(self):
        openai_api_key = getpass(prompt="Please enter your OpenAI API secret key: ")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(f"openai_api_key: {openai_api_key}\n{self.DEFAULT_CONFIG}")


    def reset_config(self):
        # TODO: Check if I even need the if below
        if not self.config_file.exists():
            self.create_config()

        with self.config_file.open(mode="w") as file:
            file.write(yaml.dump(self.DEFAULT_CONFIG, default_flow_style=False))


    def get_config(self, key):
        if not self.config_file.exists():
            self.create_config()
        with self.config_file.open(mode="r") as file:
            data = yaml.safe_load(file)
            try:
                return data[key]
            except KeyError:
                raise UsageError( # TODO: Is Usage Error a good idea here?
                    f"Key '{key}' not found in config file. Please check your config file."
                )


    def update_config(self, key, value):
        if not self.config_file.exists():
            self.create_config()

        with self.config_file.open(mode="r") as file:
            data = yaml.safe_load(file)

        data[key] = value

        with self.config_file.open(mode="w") as file:
            file.write(yaml.dump(data, default_flow_style=False))
        return value