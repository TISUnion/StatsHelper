import codecs
import collections
import json
import os
import re
import time
from urllib.request import urlopen

from mcdreforged.api.all import *

PLUGIN_METADATA = {
	'id': 'stats_helper',
	'version': '6.1.0',
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
UUIDFile = os.path.join('plugins', PluginName, 'uuid.json')
RankAmount = 15
rankColor = ['§b', '§d', '§e', '§f']
HelpMessage = '''
------MCDR {1} 插件 v{2}------
一个统计信息助手插件，可查询/排名/使用计分板列出各类统计信息
§a【格式说明】§r
§7{0}§r 显示帮助信息
§7{0} query §b<玩家> §6<统计类别> §e<统计内容> §7[<-uuid>]§r §7[<-tell>]§r
§7{0} rank §6<统计类别> §e<统计内容> §7[<-bot>]§r §7[<-tell>]§r
§7{0} scoreboard §6<统计类别> §e<统计内容> §2[<标题>] §7[<-bot>]§r
§7{0} scoreboard show/hide§r 显示/隐藏该插件的计分板
§7{0} add_player §b<玩家名>§r 将指定玩家添加至玩家uuid列表中。将添加盗版uuid
§a【参数说明】§r
§6<统计类别>§r: §6killed§r, §6killed_by§r, §6dropped§r, §6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r, §6custom§r
§6killed§r, §6killed_by§r 的 §e<统计内容> §r为 §e<生物id>§r
§6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r 的 §e<统计内容>§r 为 §e<物品/方块id>§r
§6custom§r 的 §e<统计内容>§r 详见统计信息的json文件
上述内容无需带minecraft前缀
§7[<-uuid>]§r: 用uuid替换玩家名; §7[<-bot>]§r: 统计bot与cam; §7[<-tell>]§r: 仅自己可见; §7[<-all>]§r: 列出所有项
§a【例子】§r
§7{0} query §bFallen_Breath §6used §ewater_bucket§r
§7{0} rank §6custom §etime_since_rest §7-bot§r
§7{0} scoreboard §6mined §estone§r 挖石榜
'''.strip().format(Prefix, PLUGIN_METADATA['name'], PLUGIN_METADATA['version'])

uuid_list = {}
flag_save_all = False
flag_unload = False


def name_to_uuid_fromAPI(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	js = json.loads(urlopen(url).read().decode('utf8'))
	return js['offlinesplitteduuid']


def refresh_uuid_list():
	global uuid_list
	uuid_cache = {}
	uuid_file = {}
	if not os.path.isdir(os.path.dirname(UUIDFile)):
		os.makedirs(os.path.dirname(UUIDFile))
	if os.path.isfile(UUIDFile):
		with open(UUIDFile, 'r') as file:
			uuid_file = json.load(file)
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
	for line in msg.splitlines():
		if info.is_player:
			if is_tell:
				server.tell(info.player, line)
			else:
				server.say(line)
		else:
			server.reply(info, line)


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


def get_display_text(cls, target):
	return '§6{}§r.§e{}§r'.format(cls, target)


def show_stat(server, info, name, cls, target, is_uuid, is_tell):
	global uuid_list
	uuid = name if is_uuid else uuid_list.get(name, None)
	if uuid is None:
		print_message(server, info, '玩家{}的uuid不在储存列表中'.format(name), is_tell)
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


def add_player_to_uuid_list(server, info, player):
	global uuid_list
	if player in uuid_list:
		server.reply(info, '玩家{}已在列表中'.format(player))
		return
	try:
		uuid = name_to_uuid_fromAPI(player)
	except:
		server.reply(info, '无法获得玩家{}的uuid'.format(player))
		raise
	else:
		uuid_list[player] = uuid
		save_uuid_list()
		server.reply(info, '玩家{}添加成功, uuid为{}'.format(player, uuid))


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
			print_message(server, info, HelpMessage)
		return

	cmdlen = len(command)

	@new_thread(PLUGIN_METADATA['id'])
	def inner():
		# !!stats query [玩家] [统计类别] [统计内容] (-uuid)
		if cmdlen == 5 and command[1] == 'query':
			show_stat(server, info, command[2], command[3], command[4], is_uuid, is_tell)

		# !!stats rank [统计类别] [统计内容] (过滤bot前缀)
		elif cmdlen == 4 and command[1] == 'rank':
			return show_rank(server, info, command[2], command[3], list_bot, is_tell, is_all, is_called)

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
			print_message(server, info, '参数错误！请输入{}以获取插件帮助'.format(Prefix))

	inner()


def on_unload(server):
	global flag_unload
	flag_unload = True


def on_player_joined(server, player, info):
	refresh_uuid_list()


def on_load(server: ServerInterface, old_module):
	server.register_help_message(Prefix, '查询统计信息并管理计分板')
	refresh_uuid_list()
	server.logger.info('UUID list size: {}'.format(len(uuid_list)))
