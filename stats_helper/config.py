import os

from mcdreforged.api.utils.serializer import Serializable


class Config(Serializable):
	server_path: str = './server'
	world_folder: str = 'world'
	save_world_on_query: bool = False
	save_world_on_rank: bool = False
	save_world_on_scoreboard: bool = True

	def get_world_path(self) -> str:
		return os.path.join(self.server_path, self.world_folder)

	__instance: 'Config' = None

	@classmethod
	def set_instance(cls, inst: 'Config'):
		cls.__instance = inst

	@classmethod
	def get_instance(cls) -> 'Config':
		return cls.__instance
