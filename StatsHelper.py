# -*- coding: utf-8 -*-

import json
import os
import urllib2

worldpath = 'server/world/'
prefix = '!!stats'
helpmsg = '''------MCD StatsHelper插件------
命令帮助如下:
''' + prefix + ''' 显示帮助信息
''' + prefix + ''' [玩家] [统计类别] [统计内容] (-uuid)
例子：!!stats Fallen_Breath used water_bucket
--------------------------------'''
errmsg_arg = '参数错误！请输入'+prefix+'以获取插件帮助'
errmsg_file = '未找到该玩家的统计文件！'
errmsg_target = '未找到该统计项！'
errmsg_load = '统计文件读取失败！'

def name_to_uuid(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	response=urllib2.urlopen(url)
	data = response.read()
	j=json.loads(str(data))
	return j['offlinesplitteduuid']

def print_msg(server, info, str):
	if info.isPlayer:
		server.tell(info.player, str)
	else:
		print str

def show_stats(server, info, name, classification, target, isuuid):
	uuid = name
	if not isuuid:
		uuid = name_to_uuid(uuid)
#	print 'uuid = ',uuid
	jsonfile = worldpath + 'stats/' + uuid + '.json'
	if not os.path.isfile(jsonfile):
		print_msg(server, info, errmsg_file)
		return
		
	if classification.startswith('minecraft:'):
		classification = classification.strip('minecraft:')
	if target.startswith('minecraft:'):
		target = target.strip('minecraft:')
		
	with open(jsonfile, "r") as f:
		try:
#			print 'try to read ',jsonfile
			j = json.load(f)
		except ValueError:
			print_msg(server, info, errmsg_load)
			return
		try:
			data = j['stats']['minecraft:'+classification]['minecraft:'+target]
		except KeyError:
			print_msg(server, info, errmsg_target)
			return

		msg = '玩家' + name + '的统计信息[' + classification + '-' + target + ']的值为[' + str(data) + ']'
		print_msg(server, info, msg)

def onServerInfo(server, info):
	content = info.content
	if not info.isPlayer and content.endswith('<--[HERE]'):
		content = content.strip('<--[HERE]')
	command = content.split()
#	print 'command = ', command
	if command[0] != prefix:
		return
	del command[0]
	
	cmdlen = len(command)
	if cmdlen == 0:
		for line in helpmsg.splitlines():
			print_msg(server, info, line)
		return
	
	isuuid = 0
	if command[cmdlen-1] == '-uuid':
		isuuid = true
		del command[cmdlen-1]
		cmdlen -=1
		
	if cmdlen == 3:
		show_stats(server, info, command[0], command[1], command[2], isuuid)
	else:
		print_msg(server, info, errmsg_arg)
