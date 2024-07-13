from dotenv import dotenv_values
from pathlib import Path
import os

ENV_FILENAME = ".publisher"


def load_config():
    # Load the required environment variables from the config file in ~/.publisher
    # And then merge with the environment variables from the system
    # This allows the user to override the config file with environment variables
    # This is useful for CI/CD pipelines
    out = {}
    home = str(Path.home())
    out = dotenv_values(home + "/" + ENV_FILENAME)
    out = dict(out)  # Convert OrderedDict to an actual dictionary
    return {**out, **os.environ}


print(load_config())
