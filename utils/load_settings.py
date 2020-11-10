"""
Function to load central settings from settings/secrets.yml

"""

import os
import yaml
from typing import Dict, Any


def load_settings() -> Dict[Any, Any]:

    # Make paths
    path_to_system = os.getcwd().split("meter_system")[0]
    basepath = os.path.join(path_to_system, "meter_system")
    secrets_path = os.path.join(basepath, "settings", "secrets.yaml")

    with open(secrets_path) as f:
        settings = yaml.load(f, Loader=yaml.FullLoader)
        return settings


if __name__ == '__main__':
    r = load_settings()
    print(r['integration']['pipe_name'])
