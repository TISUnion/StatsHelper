import codecs
import collections
import json
import os
import re
import shutil
import time
from typing import Optional, List, Tuple, Union, Callable, Any, Dict

from mcdreforged.api.all import *

from stats_helper import constants, utils, quick_scoreboard
from stats_helper.cmd_node import ArgumentEnding, Arguments, NameAndArgumentEnding
from stats_helper.cmd_node import ScoreboardQuery, UnknownQuickScoreboard
# assigned in on_load
from stats_helper.quick_scoreboard import Scoreboard

PLUGIN_ID = None  # type: Optional[str]
HelpMessage = None  # type: Optional[str]

uuid_list: Dict[str, str] = {}  # player -> uuid
UUID_LIST_ITEM = Tuple[str, str]
flag_save_all = False
flag_unload = False

stored = quick_scoreboard.stored


def refresh_uuid_list(server: ServerInterface):
	global uuid_list
	uuid_cache = {}
	uuid_file = {}

	# compatibility
	if os.path.isfile(constants.UUIDFilePrev):
		with open(constants.UUIDFilePrev, 'r') as file:
			uuid_file.update(json.load(file))
		server.logger.info('Migrated {} uuid mapping from the previous {}'.format(len(uuid_file), os.path.basename(constants.UUIDFilePrev)))
	# compatibility ends

	if not os.path.isdir(os.path.dirname(constants.UUIDFile)):
		os.makedirs(os.path.dirname(constants.UUIDFile))
	if os.path.isfile(constants.UUIDFile):
		with open(constants.UUIDFile, 'r') as file:
			uuid_file.update(json.load(file))
	uuid_cache_time = {}
	file_name = os.path.join(constants.ServerPath, 'usercache.json')
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
	if os.path.isdir(os.path.dirname(constants.UUIDFilePrev)):
		shutil.rmtree(os.path.dirname(constants.UUIDFilePrev))


def save_uuid_list():
	global uuid_list
	uuid_list = dict(sorted(uuid_list.items(), key=lambda x: x[0].capitalize()))
	with open(constants.UUIDFile, 'w') as file:
		json.dump(uuid_list, file, indent=4)


def tr(translation_key: str, *args):
	return ServerInterface.get_instance().tr('{}.{}'.format(PLUGIN_ID, translation_key), *args)


def print_message(source: CommandSource, msg: Union[str, RTextBase], is_tell: bool = True):
	if source.is_player:
		if is_tell:
			source.reply(msg)
		else:
			source.get_server().say(msg)
	else:
		source.reply(msg)


def get_player_list(list_bot: bool) -> List[UUID_LIST_ITEM]:
	global uuid_list
	ret = []
	for item in uuid_list.items():
		if list_bot or not utils.isBot(item[0]):
			ret.append(item)
	return ret


def trigger_save_all(server: ServerInterface):
	global flag_save_all
	flag_save_all = False
	server.execute('save-all')
	while not flag_save_all and not flag_unload:
		time.sleep(0.01)


def show_help(source: CommandSource):
	help_msg_rtext = RTextList()
	symbol = 0
	for line in HelpMessage.splitlines(True):
		result = re.search(r'(?<=§7)' + constants.Prefix + r'[\S ]*?(?=§)', line)
		if result is not None and symbol != 2:
			help_msg_rtext.append(RText(line).c(RAction.suggest_command, result.group()).h(tr('click_to_fill', result.group())))
			symbol = 1
		else:
			help_msg_rtext.append(line)
			if symbol == 1:
				symbol += 1
	source.reply(help_msg_rtext)


def get_display_text(cls: str, target: str) -> RTextBase:
	return RTextList(RText(cls, color=RColor.gold), '.', RText(target, color=RColor.yellow))


def show_stat(source: CommandSource, name: str, cls: str, target: str, is_uuid: bool, is_tell: bool):
	global uuid_list
	uuid = name if is_uuid else uuid_list.get(name, None)
	if uuid is None:
		print_message(source, tr('player_uuid_not_found', name), is_tell=is_tell)
	msg = tr('player_stat_display', name, get_display_text(cls, target), utils.get_stat_data(uuid, cls, target))
	print_message(source, msg, is_tell=is_tell)


def show_rank(source: CommandSource, cls: str, target: str, list_bot: bool, is_tell: bool, is_all: bool, is_called: bool = False):
	player_list = get_player_list(list_bot)
	arr = []
	sum = 0
	for name, uuid in player_list:
		value = utils.get_stat_data(uuid, cls, target)
		if value is not None:
			arr.append(collections.namedtuple('T', 'name value')(name, value))
			sum += value

	if len(arr) == 0:
		if not is_called:
			print_message(source, tr('stat_not_found'))
		return None
	arr.sort(key=lambda x: x.name, reverse=True)
	arr.sort(key=lambda x: x.value, reverse=True)

	show_range = min(constants.RankAmount + is_all * len(arr), len(arr))
	if not is_called:
		print_message(source, tr('show_rank.title', get_display_text(cls, target), sum, show_range), is_tell=is_tell)
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
			print_message(source, utils.get_rank_color(i) + text, is_tell=is_tell)

	ret.append('Total: ' + str(sum))
	return '\n'.join(ret)


def show_scoreboard(server: ServerInterface):
	server.execute('scoreboard objectives setdisplay sidebar ' + constants.ScoreboardName)


def hide_scoreboard(server: ServerInterface):
	server.execute('scoreboard objectives setdisplay sidebar')


def build_scoreboard(source: CommandSource, cls: str, target: str, title: Optional[str] = None, list_bot: bool = False):
	server = source.get_server()
	player_list = get_player_list(list_bot)
	trigger_save_all(server)
	server.execute('scoreboard objectives remove {}'.format(constants.ScoreboardName))
	if title is None:
		title = get_display_text(cls, target)
	else:
		title = RTextBase.from_any(title)
	server.execute('scoreboard objectives add {} minecraft.{}:minecraft.{} {}'.format(constants.ScoreboardName, cls, target, title.to_json_str()))
	for name, uuid in player_list:
		value = utils.get_stat_data(uuid, cls, target)
		if value is not None:
			server.execute('scoreboard players set {} {} {}'.format(name, constants.ScoreboardName, value))
	show_scoreboard(server)


def save_scoreboard(source: CommandSource, alias: str, cls: str, target: str, title: Optional[str] = None):
	to_save = quick_scoreboard.Scoreboard(alias, cls, target, title)
	is_succeeded = stored.append(to_save)
	if is_succeeded:
		source.reply(tr('save_scoreboard.done', alias))
	else:
		source.reply(RText(tr('save_scoreboard.duplicated', alias)).c(RAction.run_command, f'{constants.Prefix} list').h(tr('list_scoreboard.promote')))


def rm_scoreboard(source: CommandSource, alias: str):
	is_succeeded = stored.remove(alias)
	if is_succeeded:
		source.reply(tr('rm_scoreboard.done', alias))
	else:
		source.reply(RText(tr('rm_scoreboard.not_found', alias)).c(RAction.run_command, f'{constants.Prefix} list').h(tr('list_scoreboard.promote')))


def list_quick_scoreboard(source: CommandSource, is_tell: bool):
	saved_list = stored.list_scoreboard()
	print_text = RTextList()
	print_text.append(tr('list_scoreboard.summary') + RText('[+]', color=RColor.green).c(RAction.suggest_command, f'{constants.Prefix} save ').h('list_scoreboard.add') + '\n')
	num = 0
	if len(saved_list) == 0:
		print_text.append(tr('list_scoreboard.empty'))
	else: 
		for s in saved_list:
			num += 1
			display = tr('list_scoreboard.cls_target') + ': ' + get_display_text(s.cls, s.target)
			if s.title is not None:
				display += ' §2{}§r: {}'.format(tr('list_scoreboard.title'), s.title)
			print_text.append(RTextList(
				RText('[x] ', RColor.dark_red).c(RAction.suggest_command, f'{constants.Prefix} del {s.alias}').h(tr('list_scoreboard.delete', s.alias)),
				RText(f'§d{s.alias}§r {display}').c(RAction.run_command, f'{constants.Prefix} scoreboard {s.alias}').h(tr('list_scoreboard.show', s.alias))
			))
			if num < len(saved_list):
				print_text.append('\n')
	print_message(source, print_text, is_tell=is_tell)


def add_player_to_uuid_list(source: CommandSource, player: str):
	global uuid_list
	if player in uuid_list:
		source.reply(tr('add_player.player_existed', player))
		return
	try:
		uuid = utils.name_to_uuid_fromAPI(player)
	except:
		source.reply(tr('add_player.get_uuid_failed', player))
		raise
	else:
		uuid_list[player] = uuid
		save_uuid_list()
		source.reply(tr('add_player.done', player, uuid))


def register_command(server: PluginServerInterface):
	def exe(node: ArgumentNode, callback: Callable[[CommandContext, Arguments], Any]) -> ArgumentNode:
		return node.runs(lambda src, ctx: callback(ctx, Arguments.empty())).\
			then(ArgumentEnding('args').runs(lambda src, ctx: callback(ctx, ctx['args'])))

	@new_thread(PLUGIN_ID + ' show stat')
	def _show_stat(ctx: CommandContext, args: Arguments):
		ref = ctx['cls/alias']  # type: Union[Scoreboard, Tuple[str, str]]
		if isinstance(ref, Scoreboard):
			show_stat(ctx.source, ctx['player'], ref.cls, ref.target, is_uuid=args.is_uuid, is_tell=args.is_tell)
		else:
			show_stat(ctx.source, ctx['player'], ref[0], ref[1], is_uuid=args.is_uuid, is_tell=args.is_tell)

	@new_thread(PLUGIN_ID + ' show rank')
	def _show_rank(ctx: CommandContext, args: Arguments):
		ref = ctx['cls/alias']  # type: Union[Scoreboard, Tuple[str, str]]
		if isinstance(ref, Scoreboard):
			show_rank(ctx.source, ref.cls, ref.target, list_bot=args.is_bot, is_tell=args.is_tell, is_all=args.is_all)
		else:
			show_rank(ctx.source, ref[0], ref[1], list_bot=args.is_bot, is_tell=args.is_tell, is_all=args.is_all)

	def _list_quick_scoreboard(ctx: CommandContext, args: Arguments):
		list_quick_scoreboard(ctx.source, is_tell=args.is_tell)

	@new_thread(PLUGIN_ID + ' build scoreboard')
	def _build_scoreboard(ctx: CommandContext, title: Optional[str], args: Arguments):
		ref = ctx['cls/alias']  # type: Union[Scoreboard, Tuple[str, str]]
		if isinstance(ref, Scoreboard):
			build_scoreboard(ctx.source, ref.cls, ref.target, ref.title, list_bot=args.is_bot)
		else:
			build_scoreboard(ctx.source, ref[0], ref[1], title, list_bot=args.is_bot)

	server.register_command(
		Literal(constants.Prefix).
		runs(show_help).
		on_error(UnknownArgument, lambda src: src.reply(
			RText(tr('command.unknown_argument')).c(RAction.run_command, constants.Prefix)
		), handled=True).
		on_child_error(UnknownQuickScoreboard, lambda src: src.reply(
			RText(tr('command.unknown_scoreboard')).c(RAction.run_command, f'{constants.Prefix} list')
		)).

		# !!stats query [玩家] [统计类别] [统计内容] [<-args>]
		# !!stats query [玩家] [保存的统计项] [<-args>]
		then(Literal('query').then(
			Text('player').then(
				exe(ScoreboardQuery('cls/alias'), _show_stat)
			)
		)).
		# !!stats rank [统计类别] [统计内容] [<-args>]
		# !!stats rank [保存的统计项] [<-args>]
		then(Literal('rank').then(
			exe(ScoreboardQuery('cls/alias'), _show_rank)
		)).
		then(exe(Literal('list'), _list_quick_scoreboard)).
		# !!stats save [要保存的统计项] [统计类别] [统计内容] [<标题>]
		then(Literal('save').then(
			Text('alias').then(
				Text('cls').then(
					Text('target').
					runs(lambda src, ctx: save_scoreboard(src, ctx['alias'], ctx['cls'], ctx['target'], None)).
					then(
						QuotableText('title').
						runs(lambda src, ctx: save_scoreboard(src, ctx['alias'], ctx['cls'], ctx['target'], ctx['title']))
					)
				)
			)
		)).
		then(Literal('del').then(
			Text('alias').runs(
				lambda src, ctx: rm_scoreboard(src, ctx['del'])
			)
		)).

		then(
			Literal('scoreboard').
			then(Literal('show').runs(lambda src: show_scoreboard(src.get_server()))).
			then(Literal('hide').runs(lambda src: hide_scoreboard(src.get_server()))).
			# !!stats scoreboard [统计类别] [统计内容] [<标题>] [<-args>]
			# !!stats [保存的统计项] [<-args>]
			then(
				ScoreboardQuery('cls/alias').
				runs(lambda src, ctx: _build_scoreboard(ctx, None, Arguments.empty())).
				then(NameAndArgumentEnding('title/args').runs(
					lambda src, ctx: _build_scoreboard(ctx, ctx['title/args'][0], ctx['title/args'][1]))
				)
			)
		).
		then(Literal('add_player').then(
			Text('player').runs(
				lambda src, ctx: add_player_to_uuid_list(src, ctx['player'])
			)
		))
	)


def on_info(server: PluginServerInterface, info: Info):
	if not info.is_user:
		if info.content == 'Saved the game':
			global flag_save_all
			flag_save_all = True


def on_unload(server: PluginServerInterface):
	global flag_unload
	flag_unload = True


def on_player_joined(server: PluginServerInterface, player: str, info: Info):
	refresh_uuid_list(server)


def on_load(server: PluginServerInterface, old_module):
	global PLUGIN_ID, HelpMessage
	PLUGIN_ID = server.get_self_metadata().id
	server.register_help_message(constants.Prefix, tr('summary_help'))
	HelpMessage = tr('help_message').strip().format(
		name=server.get_self_metadata().name,
		version=server.get_self_metadata().version,
		prefix=constants.Prefix,
	)
	stored.load(server.logger)
	refresh_uuid_list(server)
	server.logger.info('UUID list size: {}'.format(len(uuid_list)))
	register_command(server)
