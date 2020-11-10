"""
Function to load central settings from settings/secrets.yml

"""

import os
import yaml
from typing import Dict, Any


def load_settings() -> Dict[Any, Any]:
    p = os.path.abspath('../settings/secrets.yaml')
    with open(p) as f:
        settings = yaml.load(f, Loader=yaml.FullLoader)
        print(settings)
        return settings


if __name__ == '__main__':
    r = load_settings()
    print(r['integration']['pipe_name'])
