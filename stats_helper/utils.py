import json
import os
import re
from typing import Optional
from urllib.request import urlopen

from stats_helper import constants, config
from stats_helper.config import Config


def name_to_uuid_fromAPI(name):
    url = 'http://tools.glowingmines.eu/convertor/nick/' + name
    js = json.loads(urlopen(url).read().decode('utf8'))
    return js['offlinesplitteduuid']


def isBot(name: str):
    black_keys = config.black_keys
    if len(name) < 4 or len(name) > 16:
        return True
    for black_key in black_keys:
        if re.search(black_key, name, re.IGNORECASE):
            return True
    return False


def get_stat_data(uuid: str, cls: str, target: str) -> Optional[int]:
    try:
        with open(os.path.join(Config.get_instance().get_world_path(), 'stats', uuid + '.json'), 'r') as f:
            return json.load(f)['stats']['minecraft:' + cls]['minecraft:' + target]
    except:
        return None


def get_rank_color(rank: int) -> str:
    """
    rank starts from 0
    """
    return constants.rankColor[min(rank, len(constants.rankColor) - 1)]
