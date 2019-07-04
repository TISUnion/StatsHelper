# -*- coding: utf-8 -*-

import json
import os
import urllib2

worldpath = 'server/world/'
prefix = '!!stats'
debug_output = 0
help_msg = '''------MCD StatsHelper插件------
命令帮助如下:
''' + prefix + ''' 显示帮助信息
''' + prefix + ''' [玩家] [统计类别] [统计内容] (-uuid)

[统计类别]与[统计内容]
killed, killed_by, dropped, picked_up, used, mined, broken, custom
killed, killed_by 的[统计内容]为生物id
picked_up, used, mined, broken 的[统计内容]为物品/方块id
custom 的[统计内容]详见统计信息的json文件

例子：
''' + prefix + ''' Fallen_Breath used water_bucket
''' + prefix + ''' 85dbd009-69ed-3cc4-b6b6-ac1e6d07202e killed zombie -uuid
''' + prefix + ''' chino_desu custom time_since_death
'''
errmsg_arg = '参数错误！请输入'+prefix+'以获取插件帮助'
errmsg_file = '未找到该玩家的统计文件！'
errmsg_target = '未找到该统计项！'
errmsg_load = '统计文件读取失败！'

def name_to_uuid(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	response = urllib2.urlopen(url)
	data = response.read()
	j = json.loads(str(data))
	return j['offlinesplitteduuid']


def print_msg(server, info, msg):
	for line in msg.splitlines():
		if info.isPlayer:
			server.tell(info.player, line)
		else:
			print line
			
def debug_print(server, info, msg):
	if debug_output:
		print_msg(server, info, '[StatsHelper]' + msg)
		
def debug_print_list(server, info, msg, lst):
	if debug_output:
		debug_print(server, info, msg)
		for i in lst:
			debug_print(server, info, '    ' + i)

def show_stats(server, info, name, classification, target, isuuid):
	uuid = name
	if not isuuid:
		uuid = name_to_uuid(uuid)
	debug_print(server, info, 'uuid = ' + uuid)
		
	jsonfile = worldpath + 'stats/' + uuid + '.json'
	if not os.path.isfile(jsonfile):
		print_msg(server, info, errmsg_file)
		return
		
	if classification.startswith('minecraft:'):
		classification = classification.strip('minecraft:')
	if target.startswith('minecraft:'):
		target = target.strip('minecraft:')
		
#	jsonfile='server/a.json'
	with open(jsonfile, "r") as f:
		try:
			debug_print(server, info, 'trying to read ' + jsonfile)
			j = json.load(f)
		except ValueError:
			print_msg(server, info, errmsg_load)
			return
		try:
			data = j['stats']['minecraft:'+classification]['minecraft:'+target]
		except KeyError:
			print_msg(server, info, errmsg_target)
			return

		msg = '玩家' + name + '的统计信息[' + classification + '.' + target + ']的值为[' + str(data) + ']'
		print_msg(server, info, msg)

def onServerInfo(server, info):
	content = info.content
	if not info.isPlayer and content.endswith('<--[HERE]'):
		content = content.strip('<--[HERE]')
		
	command = content.split()
	if command[0] != prefix:
		return
	debug_print_list(server, info, 'raw command = ' , command)
	del command[0]
	
	cmdlen = len(command)
	if cmdlen == 0:
		print_msg(server, info, help_msg)
		return
	
	isuuid = 0
	if command[cmdlen-1] == '-uuid':
		isuuid = 1
		del command[cmdlen-1]
		cmdlen -= 1
	
	debug_print_list(server, info, 'processed command = ', command)
	if cmdlen == 3:
		show_stats(server, info, command[0], command[1], command[2], isuuid)
	else:
		print_msg(server, info, errmsg_arg)
