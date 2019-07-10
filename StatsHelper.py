# -*- coding: utf-8 -*-

import json
import os
import urllib2

serverpath = 'server/'
worldpath = serverpath + 'world/'
prefix = '!!stats'
debug_output = 0
rank_amount = 15
help_msg = '''------MCD StatsHelper插件 v1.2------
§a【格式说明】§r
§7''' + prefix + '''§r 显示帮助信息
§7''' + prefix + ''' query §b[玩家] §6[统计类别] §e[统计内容] §7(-uuid)§r §7(-tell)§r
§7''' + prefix + ''' rank §6[统计类别] §e[统计内容] §7(-bot)§r §7(-tell)§r
§a【参数说明】§r
§6[统计类别]§r: §6killed§r, §6killed_by§r, §6dropped§r, §6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r, §6custom§r
§6killed§r, §6killed_by§r 的§e[统计内容]§r为§e[生物id]§r
§6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r 的§e[统计内容]为§e[物品/方块id]§r
§6custom§r 的§e[统计内容]§r详见统计信息的json文件
上述内容无需带minecraft前缀
§7(-uuid)§r: 用uuid替换玩家名; §7(-bot)§r: 统计bot与cam; §7(-tell)§r: 仅自己可见
§a【例子】§r
§7''' + prefix + ''' query §bFallen_Breath §6used §ewater_bucket§r
§7''' + prefix + ''' query §b85dbd009-69ed-3cc4-b6b6-ac1e6d07202e §6killed §ezombie §7-uuid§r
§7''' + prefix + ''' rank §6mined §estone §7-tell§r
§7''' + prefix + ''' rank §6custom §etime_since_rest §7-bot§r
'''
errmsg_arg = '参数错误！请输入'+prefix+'以获取插件帮助'
errmsg_file = '未找到该玩家的统计文件！'
errmsg_target = '未找到该统计项！'
errmsg_load = '统计文件读取失败！'

def debug_print(server, info, msg):
	if debug_output:
		print_msg(server, info, '[StatsHelper]' + msg)
		
def debug_print_list(server, info, msg, lst):
	if debug_output:
		debug_print(server, info, msg)
		for i in lst:
			debug_print(server, info, '    ' + i)
			
def name_to_uuid_fromAPI(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	response = urllib2.urlopen(url)
	data = response.read()
	js = json.loads(str(data))
	return js['offlinesplitteduuid']
	
def name_to_uuid(server, info, name):
	filename = serverpath + 'usercache.json'
	if os.path.isfile(filename):
		with open(filename, 'r') as f:
			try:
				js = json.load(f)
			except ValueError:
				print_msg(server, info, 'cann\'t open json file '+filename)
				return name_to_uuid_fromAPI(name)
			for i in js:
				if i['name'] == name:
					return i['uuid']
	print_msg(server, info, 'name not found, use API')
	return name_to_uuid_fromAPI(name)

def print_msg(server, info, msg, istell = True):
	for line in msg.splitlines():
		if info.isPlayer:
			if istell:
				server.tell(info.player, line)
			else:
				server.say(line)
		else:
			print line

def show_stats(server, info, name, classification, target, isuuid, istell):
	uuid = name
	if not isuuid:
		uuid = name_to_uuid(server, info, uuid)
	debug_print(server, info, 'uuid = ' + uuid)
		
	jsonfile = worldpath + 'stats/' + uuid + '.json'
	if not os.path.isfile(jsonfile):
		print_msg(server, info, errmsg_file)
		return
		
#	jsonfile='server/a.json'
	with open(jsonfile, 'r') as f:
		try:
			debug_print(server, info, 'trying to read ' + jsonfile)
			j = json.load(f)
		except ValueError:
			print_msg(server, info, errmsg_load)
			return
		try:
			data = j['stats']['minecraft:' + classification]['minecraft:' + target]
		except KeyError:
			print_msg(server, info, errmsg_target)
			return

		msg = '玩家§b' + name + '§r的统计信息[§6' + classification + '§r.§e' + target + '§r]的值为§a' + str(data) + '§r'
		print_msg(server, info, msg, istell)

def isbot(name):
	blacklist = 'A_Pi#nw#sw#SE#ne#nf#SandWall#storage#zi_ming###'
	blackkey = ['farm', 'bot_', 'cam', '_b']
	if blacklist.find(name) >= 0: return True
	if len(name) <= 4 or len(name) > 16: return True
	for i in blackkey:
		if name.find(i) >= 0:
			return True
	return False
		
def show_rank(server, info, classification, target, listbot, istell):
	filename = serverpath + 'usercache.json'
	
	if os.path.isfile(filename):
		with open(filename, 'r') as f:
			try:
				js = json.load(f)
			except ValueError:
				print_msg(server, info, 'cann\'t open json file ' + filename)
				return name_to_uuid_fromAPI(name)
			arr = []
			for i in js:
				name = i['name']
				if not listbot and isbot(name):
					continue
				jsonfile = worldpath + 'stats/' + i['uuid'] + '.json'
				if os.path.isfile(jsonfile):
					with open(jsonfile, 'r') as f2:
						try:
							if debug_output > 1: debug_print(server, info, 'trying to read ' + jsonfile)
							j2 = json.load(f2)
						except ValueError:
							pass
						try:
							data = int(j2['stats']['minecraft:' + classification]['minecraft:' + target])
						except KeyError:
							data = -1
						if data >= 0:
							if debug_output > 1: debug_print(server, info, 'append [' + name + ', ' + str(data) + ']')
							arr.append((name, data))
					
		if len(arr) == 0:
			print_msg(server, info, errmsg_target)
			return
		arr.sort(key = lambda x:x[0])
		arr.reverse()
		arr.sort(key = lambda x:x[1])
		arr.reverse()
		
		print_msg(server, info, '统计信息[§6' + classification + '§r.§e' + target + '§r]的前十五名为', istell)
		maxnamelen = 0
		for i in range(0, min(rank_amount, len(arr))):
			maxnamelen = max(maxnamelen, len(str(arr[i][1])))
		for i in range(0, min(rank_amount, len(arr))):
			print_msg(server, info, '#' + str(i + 1) + ' ' * (3-len(str(i + 1))) + str(arr[i][1]) + ' ' * (maxnamelen - len(str(arr[i][1])) + 1) + arr[i][0], istell)
	else:
		print_msg(server, info, 'usercache.json not found')

def onServerInfo(server, info):
	content = info.content
	isuuid = content.find('-uuid') >= 0
	content = content.replace('-uuid', '')
	listbot = content.find('-bot') >= 0
	content = content.replace('-bot', '')
	istell = content.find('-tell') >= 0
	content = content.replace('-tell', '')
	if not info.isPlayer and content.endswith('<--[HERE]'):
		content = content.replace('<--[HERE]', '')
		
	command = content.split()
	if command[0] != prefix:
		return
	debug_print(server, info, 'raw content = ' + info.content)
	debug_print_list(server, info, 'raw command = ' , command)
	del command[0]
	
	if len(command) == 0:
		print_msg(server, info, help_msg)
		return
	
	
	cmdlen = len(command)
	debug_print_list(server, info, 'processed command = ', command)
	debug_print(server, info, '[isuuid, listbot] = [' + str(isuuid) + ', ' + str(listbot) + ']')
	if cmdlen == 4 and command[0] == 'query':
	# !!stats query [玩家] [统计类别] [统计内容] (-uuid)
		show_stats(server, info, command[1], command[2], command[3], isuuid, istell)
	elif command[0] == 'rank':
	# !!stats rank [统计类别] [统计内容] (过滤bot前缀)
		if cmdlen == 3 or cmdlen == 4:
			show_rank(server, info, command[1], command[2], listbot, istell)
		else:
			print_msg(server, info, errmsg_arg)
	else:
		print_msg(server, info, errmsg_arg)
