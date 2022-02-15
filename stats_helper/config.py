import os
from typing import List

from mcdreforged.api.utils.serializer import Serializable


class Config(Serializable):
	server_path: str = './server'
	world_folder: str = 'world'
	save_world_on_query: bool = False
	save_world_on_rank: bool = False
	save_world_on_scoreboard: bool = True
	black_keys: List[str] = [r'farm', r'bot_', r'cam', r'_b_', r'bot-', r'bot\d', r'^bot', r'A_Pi', r'nw', r'sw', r'SE',
							 r'ne', r'nf', r'SandWall', r'storage', r'Steve', r'Alex', r'DuperMaster', r'Nya_Vanilla', r'Witch', r'Klio_5']

	def get_world_path(self) -> str:
		return os.path.join(self.server_path, self.world_folder)

	__instance: 'Config' = None

	@classmethod
	def set_instance(cls, inst: 'Config'):
		cls.__instance = inst

	@classmethod
	def get_instance(cls) -> 'Config':
		return cls.__instance
