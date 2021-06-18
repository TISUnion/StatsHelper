import codecs
import collections
import json
import os
import re
import shutil
import time
from threading import RLock
from typing import Optional, List, Dict
from urllib.request import urlopen

from mcdreforged.api.all import *

PLUGIN_METADATA = {
	'id': 'stats_helper',
	'version': '6.2-alpha6',
	'name': 'Stats helper',
	'description': 'A Minecraft statistic helper',
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/TISUnion/StatsHelper'
}

ServerPath = 'server'
WorldPath = os.path.join(ServerPath, 'world')
Prefix = '!!stats'
PluginName = 'StatsHelper'
ScoreboardName = PluginName
UUIDFile = os.path.join('config', PluginName, 'uuid.json')
UUIDFilePrev = os.path.join('plugins', PluginName, 'uuid.json')
SavedScoreboardFile = os.path.join('config', PluginName, 'saved_scoreboard.json')
RankAmount = 15
rankColor = ['§b', '§d', '§e', '§f']
HelpMessage = '''
------MCDR {1} 插件 v{2}------
一个统计信息助手插件，可查询/排名/使用计分板列出各类统计信息
§a【格式说明】§r
§7{0}§r 显示帮助信息
§7{0}§r §d<代名> §7[<-bot>]§r 快速调出一个保存的计分板
§7{0} list §7[<-tell>] §r列出已保存的计分项信息
§7{0} save §d<代名> §6<统计类别> §e<统计内容> §2[<标题>]§r 保存快速计分
§7{0} del §d<代名> §r删除一个快速访问计分项
§7{0} query §b<玩家> §6<统计类别> §e<统计内容> §7[<-uuid>]§r §7[<-tell>]§d
§7{0} rank §6<统计类别> §e<统计内容> §7[<-bot>]§r §7[<-tell>]§r
§7{0} scoreboard §6<统计类别> §e<统计内容> §2[<标题>] §7[<-bot>]§r
§7{0} scoreboard show§r 显示该插件的计分板
§7{0} scoreboard hide§r 隐藏该插件的计分板
§7{0} add_player §b<玩家名>§r 将指定玩家添加至玩家uuid列表中。将添加盗版uuid
§a【参数说明】§r
§d<代名>§r: 可以使用§7{0} list§r查询有效的代名, 此外§7{0} query§r/§7rank§f中的§6<统计类别>§r §e<统计内容>§f可以使用§d<代名>§f替代
§6<统计类别>§r: §6killed§r, §6killed_by§r, §6dropped§r, §6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r, §6custom§r
§6killed§r, §6killed_by§r 的 §e<统计内容> §r为 §e<生物id>§r
§6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r 的 §6<统计类别>§r 为 §e<物品/方块id>§r
§6custom§r 的 §e<统计内容>§r 详见统计信息的json文件
上述内容无需带minecraft前缀
§7[<-uuid>]§r: 用uuid替换玩家名; §7[<-bot>]§r: 统计bot与cam; §7[<-tell>]§r: 仅自己可见; §7[<-all>]§r: 列出所有项
§a【例子】§r
§7{0} save fly custom aviate_one_cm 飞行榜§r
§7{0} query §bFallen_Breath §6used §ewater_bucket§r
§7{0} rank §6custom §etime_since_rest §7-bot§r
§7{0} scoreboard §6mined §estone§r 挖石榜
'''.strip().format(Prefix, PLUGIN_METADATA['name'], PLUGIN_METADATA['version'])

uuid_list = {}  # player -> uuid
flag_save_all = False
flag_unload = False
Scoreboard = collections.namedtuple('Scoreboard', 'alias cls target title')


class SavedScoreboards:
	def __init__(self, path: str) -> None:
		self.path = path
		self.saved = {}  # type: Dict[str, Scoreboard]
		self.lock = RLock()
	
	def append(self, scoreboard: Scoreboard) -> bool:
		ret = self.__append(scoreboard)
		self.save()
		return ret

	def __append(self, scoreboard: Scoreboard) -> bool:
		with self.lock:
			existed = self.get(scoreboard.alias)
			if not existed:
				self.saved[scoreboard.alias] = scoreboard
				return True
			else:
				return False

	def remove(self, alias):
		ret = self.__remove(alias)
		self.save()
		return ret

	def __remove(self, alias):
		with self.lock:
			existed = self.get(alias)
			if not existed:
				return False
			else:
				self.saved.pop(alias)
				return True

	def load(self, logger=None):
		error_log = lambda content: (logger.error if logger is not None else print)(content)
		with self.lock:
			if not os.path.isdir(os.path.dirname(self.path)):
				os.makedirs(os.path.dirname(self.path))
			self.saved.clear()
			need_save = False
			if not os.path.isfile(self.path):
				need_save = True
			else:
				with open(self.path, 'r', encoding='UTF-8') as f:
					try:
						for key, value in json.load(f).items():
							self.__append(Scoreboard(key, value['cls'], value['target'], value['title']))
					except Exception as e:
						error_log(e)
						need_save = True
			if need_save:
				self.save()

	def save(self):
		with self.lock:
			out = {}
			for key, value in self.saved.items():
				out[key] = {
					'cls': value.cls,
					'target': value.target,
					'title': value.title
				}
			with open(self.path, 'w', encoding='UTF-8') as f:
				json.dump(out, f, indent=2, ensure_ascii=False)

	def get(self, name) -> Optional[Scoreboard]:
		with self.lock:
			return self.saved.get(name)

	def list_scoreboard(self) -> List[Scoreboard]:
		with self.lock:
			return list(self.saved.values())


stored = SavedScoreboards(SavedScoreboardFile)


def name_to_uuid_fromAPI(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	js = json.loads(urlopen(url).read().decode('utf8'))
	return js['offlinesplitteduuid']


def refresh_uuid_list(server: ServerInterface):
	global uuid_list
	uuid_cache = {}
	uuid_file = {}

	# compatibility
	if os.path.isfile(UUIDFilePrev):
		with open(UUIDFilePrev, 'r') as file:
			uuid_file.update(json.load(file))
		server.logger.info('Migrated {} uuid mapping from the previous {}'.format(len(uuid_file), os.path.basename(UUIDFilePrev)))
	# compatibility ends

	if not os.path.isdir(os.path.dirname(UUIDFile)):
		os.makedirs(os.path.dirname(UUIDFile))
	if os.path.isfile(UUIDFile):
		with open(UUIDFile, 'r') as file:
			uuid_file.update(json.load(file))
	uuid_cache_time = {}
	file_name = os.path.join(ServerPath, 'usercache.json')
	if os.path.isfile(file_name):
		with codecs.open(file_name, 'r', encoding='utf8') as f:
			try:
				for item in json.load(f):
					player, uuid = item['name'], item['uuid']
					expired_time = time.strptime(item['expiresOn'].rsplit(' ', 1)[0], '%Y-%m-%d %X')
					if player in uuid_cache:
						flag = expired_time > uuid_cache_time[player]
					else:
						flag = True
					if flag:
						uuid_cache[player] = uuid
						uuid_cache_time[player] = expired_time
			except ValueError:
				pass
	uuid_list.update(uuid_file)
	uuid_list.update(uuid_cache)
	save_uuid_list()

	# compatibility
	if os.path.isdir(os.path.dirname(UUIDFilePrev)):
		shutil.rmtree(os.path.dirname(UUIDFilePrev))


def save_uuid_list():
	global uuid_list
	uuid_list = dict(sorted(uuid_list.items(), key=lambda x: x[0].capitalize()))
	with open(UUIDFile, 'w') as file:
		json.dump(uuid_list, file, indent=4)


def isBot(name: str):
	name = name.upper()
	blacklist = 'A_Pi#nw#sw#SE#ne#nf#SandWall#storage#Steve#Alex#DuperMaster#Nya_Vanilla#Witch#Klio_5#######'.upper()
	black_keys = [r'farm', r'bot_', r'cam', r'_b_', r'bot-', r'bot\d', r'^bot']
	if blacklist.find(name) >= 0 or len(name) < 4 or len(name) > 16:
		return True
	for black_key in black_keys:
		if re.search(black_key.upper(), name):
			return True
	return False


def print_message(server, info, msg, is_tell=True):
	if info.is_player:
		if is_tell:
			server.tell(info.player, msg)
		else:
			server.say(msg)
	else:
		server.reply(info, msg)


def get_stat_data(uuid, cls, target):
	try:
		with open(os.path.join(WorldPath, 'stats', uuid + '.json'), 'r') as f:
			return json.load(f)['stats']['minecraft:' + cls]['minecraft:' + target]
	except:
		return None


def get_player_list(server, info, list_bot):
	global uuid_list
	ret = []
	for i in uuid_list.items():
		if list_bot or not isBot(i[0]):
			ret.append(i)
	return ret


def trigger_save_all(server):
	global flag_save_all
	flag_save_all = False
	server.execute('save-all')
	while not flag_save_all and not flag_unload:
		time.sleep(0.01)


def show_help(server, info):
	help_msg_rtext = RTextList()
	symbol = 0
	for line in HelpMessage.splitlines(True):
		result = re.search(r'(?<=§7)' + Prefix + r'[\S ]*?(?=§)', line)
		if result is not None and symbol != 2:
			help_msg_rtext.append(RText(line).c(RAction.suggest_command, result.group()).h('点击以填入 §7{}§r'.format(result.group())))
			symbol = 1
		else:
			help_msg_rtext.append(line)
			if symbol == 1:
				symbol += 1
	server.reply(info, help_msg_rtext)


def get_display_text(cls, target):
	return '§6{}§r.§e{}§r'.format(cls, target)


def show_stat(server, info, name, cls, target, is_uuid, is_tell):
	global uuid_list
	uuid = name if is_uuid else uuid_list.get(name, None)
	if uuid is None:
		print_message(server, info, '玩家§b{}§r的uuid不在储存列表中'.format(name), is_tell)
	msg = '玩家§b{}§r的统计信息[{}]的值为§a{}§r'.format(name, get_display_text(cls, target), get_stat_data(uuid, cls, target))
	print_message(server, info, msg, is_tell)


def show_rank(server, info, cls, target, list_bot, is_tell, is_all, is_called=False):
	player_list = get_player_list(server, info, list_bot)
	arr = []
	sum = 0
	for name, uuid in player_list:
		value = get_stat_data(uuid, cls, target)
		if value is not None:
			arr.append(collections.namedtuple('T', 'name value')(name, value))
			sum += value

	if len(arr) == 0:
		if not is_called:
			print_message(server, info, '未找到该统计项或该统计项全空！')
		return None
	arr.sort(key=lambda x: x.name, reverse=True)
	arr.sort(key=lambda x: x.value, reverse=True)

	show_range = min(RankAmount + is_all * len(arr), len(arr))
	if not is_called:
		print_message(
			server, info,
			'统计信息[{}]的总数为§c{}§r，前{}名为'.format(get_display_text(cls, target), sum, show_range),
			is_tell
		)
	ret = ['{}.{}'.format(cls, target)]

	max_name_length = max([len(str(data.name)) for data in arr])
	for i in range(show_range):
		text = '#{}{}{}{}{}'.format(
			i + 1,
			' ' * (1 if is_called else 4 - len(str(i + 1))),
			arr[i].name,
			' ' * (1 if is_called else max_name_length - len(arr[i].name) + 2),
			arr[i].value
		)
		ret.append(text)
		if not is_called:
			print_message(server, info, rankColor[min(i, len(rankColor) - 1)] + text, is_tell)

	ret.append('Total: ' + str(sum))
	return '\n'.join(ret)


def show_scoreboard(server):
	server.execute('scoreboard objectives setdisplay sidebar ' + ScoreboardName)


def hide_scoreboard(server):
	server.execute('scoreboard objectives setdisplay sidebar')


def build_scoreboard(server, info, cls, target, title=None, list_bot=False):
	player_list = get_player_list(server, info, list_bot)
	trigger_save_all(server)
	server.execute('scoreboard objectives remove ' + ScoreboardName)
	if title is None:
		title = get_display_text(cls, target)
	title = json.dumps({'text': title})
	server.execute('scoreboard objectives add {} minecraft.{}:minecraft.{} {}'.format(ScoreboardName, cls, target, title))
	for name, uuid in player_list:
		value = get_stat_data(uuid, cls, target)
		if value is not None:
			server.execute('scoreboard players set {} {} {}'.format(name, ScoreboardName, value))
	show_scoreboard(server)


def save_scoreboard(server, info, alias, cls, target, title = None):
	to_save = Scoreboard(alias, cls, target, title)
	is_succeeded = stored.append(to_save)
	if is_succeeded:
		server.reply(info, f'已将统计项§d{alias}§r保存到快速访问, 请注意: 本插件并不会检查保存的统计类别是否有效!')
	else:
		server.reply(info, RText(f'快速访问列表中§c已存在§r统计项§d{alias}§r, §7点此§r查阅列表').c(RAction.run_command, f'{Prefix} list').h('点此查阅快速访问列表'))


def rm_scoreboard(server, info, alias):
	is_succeeded = stored.remove(alias)
	if is_succeeded:
		server.reply(info, f'已自快速访问中移除统计项§d{alias}§r')
	else:
		server.reply(info, RText(f'§c未找到§r快速访问统计项§d{alias}§r, §7点此§r查阅列表').c(RAction.run_command, f'{Prefix} list').h('点此查阅快速访问列表'))


def list_saved_scoreboard(server, info, is_tell):
	saved_list = stored.list_scoreboard()
	print_text = RTextList()
	print_text.append('已保存的快速访问统计项如下: ' + RText('[+]', color = RColor.green).c(RAction.suggest_command, f'{Prefix} save ').h('点此§a添加§r一个快速访问计分项') + '\n')
	num = 0
	if len(saved_list) == 0:
		print_text.append('§e还没有保存快速访问计分项呢, 点击上方绿色加号添加一个吧§r')
	else: 
		for s in saved_list:
			num += 1
			display = '统计§6类别§r/§e规则§r: ' + get_display_text(s.cls, s.target)
			if s.title is not None:
				display += f' §2标题§r: {s.title}'
			print_text.append(RText('[x] ', RColor.dark_red).c(RAction.suggest_command, f'{Prefix} del {s.alias}').h(f'点此§4删除§r快速访问计分项§d{s.alias}§r') + 
				RText(f'[§7{num}§r] §d{s.alias}§r {display}').c(RAction.run_command, f'{Prefix} {s.alias}').h(f'点击以§a显示§r计分板§d{s.alias}§r'))
			if num < len(saved_list):
				print_text.append('\n')
	print_message(server, info, print_text, is_tell)


def add_player_to_uuid_list(server, info, player):
	global uuid_list
	if player in uuid_list:
		server.reply(info, '玩家§b{}§r已在列表中'.format(player))
		return
	try:
		uuid = name_to_uuid_fromAPI(player)
	except:
		server.reply(info, '无法获得玩家§b{}§r的uuid'.format(player))
		raise
	else:
		uuid_list[player] = uuid
		save_uuid_list()
		server.reply(info, '玩家§b{}§r添加成功, uuid为§7{}§r'.format(player, uuid))


def on_info(server, info: Info, arg=None):
	is_called = arg is not None
	if not is_called and not info.is_user:
		if info.content == 'Saved the game':
			global flag_save_all
			flag_save_all = True
		return
	content = arg if is_called else info.content
	is_uuid = content.find('-uuid') >= 0
	list_bot = content.find('-bot') >= 0
	is_tell = content.find('-tell') >= 0
	is_all = content.find('-all') >= 0
	content = content.replace('-uuid', '')
	content = content.replace('-bot', '')
	content = content.replace('-tell', '')
	content = content.replace('-all', '')

	command = content.split()
	if len(command) == 0 or command[0] != Prefix:
		return

	info.cancel_send_to_server()

	if len(command) == 1:
		if not is_called:
			show_help(server, info)
		return

	cmdlen = len(command)

	@new_thread(PLUGIN_METADATA['id'])
	def inner():
		error_get_saved = False
		# !!stats query [玩家] [统计类别] [统计内容] (-uuid)
		# !!stats query [玩家] [保存的统计项] (-uuid)
		if cmdlen in [4, 5] and command[1] == 'query':
			if cmdlen == 5:
				show_stat(server, info, command[2], command[3], command[4], is_uuid, is_tell)
			else:
				scoreboard = stored.get(command[3])
				if scoreboard:
					show_stat(server, info, command[2], scoreboard.cls, scoreboard.target, is_uuid, is_tell)
				else:
					error_get_saved = True

		# !!stats rank [统计类别] [统计内容] (过滤bot前缀)
		# !!stats rank [保存的统计项] (过滤bot前缀)
		elif cmdlen in [3, 4] and command[1] == 'rank':
			if cmdlen == 4:
				return show_rank(server, info, command[2], command[3], list_bot, is_tell, is_all, is_called)
			else:
				scoreboard = stored.get(command[2])
				if scoreboard:
					show_rank(server, info, scoreboard.cls, scoreboard.target, list_bot, is_tell, is_all, is_called)

		# !!stats list
		elif cmdlen == 2 and command[1] == 'list':
			list_saved_scoreboard(server, info, is_tell)

		# !!stats save [要保存的统计项] [统计类别] [统计内容] [<标题>]
		elif cmdlen in [5, 6] and command[1] == 'save':
			title = None
			if cmdlen == 6:
				title = command[5]
			save_scoreboard(server, info, command[2], command[3], command[4], title)

		# !!stats del [要删除的统计项]
		elif cmdlen == 3 and command[1] == 'del':
			rm_scoreboard(server, info, command[2])

		# !!stats [保存的统计项] (过滤bot前缀)
		elif cmdlen == 2 and stored.get(command[1]):
			scoreboard = stored.get(command[1])
			if scoreboard:
				build_scoreboard(server, info, scoreboard.cls, scoreboard.target, scoreboard.title, list_bot)
			else:
				error_get_saved = True
				
		# !!stats scoreboard [统计类别] [统计内容] [<标题>] (过滤bot前缀)
		elif cmdlen in [4, 5] and command[1] == 'scoreboard':
			title = command[4] if cmdlen == 5 else None
			build_scoreboard(server, info, command[2], command[3], title=title, list_bot=list_bot)

		# !!stats scoreboard show
		elif cmdlen == 3 and command[1] == 'scoreboard' and command[2] == 'show':
			show_scoreboard(server)

		# !!stats scoreboard hide
		elif cmdlen == 3 and command[1] == 'scoreboard' and command[2] == 'hide':
			hide_scoreboard(server)

		# !!stats add_player [玩家名]
		elif cmdlen == 3 and command[1] == 'add_player':
			add_player_to_uuid_list(server, info, command[2])

		else:
			print_message(server, info, RText('§c参数错误！§7点此§r以获取插件帮助'.format(Prefix)).c(RAction.run_command, Prefix).h('查阅插件帮助'))

		if error_get_saved:
			server.reply(info, RText('§c未在快速访问列表中找到该统计项! §7点此§r查阅列表').c(RAction.run_command, f'{Prefix} list').h('查阅快速访问列表'))
	inner()


def on_unload(server):
	global flag_unload
	flag_unload = True


def on_player_joined(server, player, info):
	refresh_uuid_list(server)


def on_load(server: ServerInterface, old_module):
	server.register_help_message(Prefix, '查询统计信息并管理计分板')
	stored.load(server.logger)
	refresh_uuid_list(server)
	server.logger.info('UUID list size: {}'.format(len(uuid_list)))
