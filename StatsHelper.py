# -*- coding: utf-8 -*-

import json
import os
import urllib2

worldpath = 'world/'
prefix = '!!stats'
helpmsg = '''------MCD StatsHelper插件------
命令帮助如下:
''' + prefix + ''' 显示帮助信息
''' + prefix + ''' [玩家] [统计类别] [统计内容名称] (-uuid) 显示[玩家]
--------------------------------'''
errmsg_arg = '参数错误！请输入'+prefix+'以获取插件帮助'
errmsg_file = '未找到该玩家的统计文件'
errmsg_target = '参数错误！请输入'+prefix+'以获取插件帮助'

def name_to_uuid(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	response=urllib2.urlopen(url)
	data = response.read()
	j=json.loads(str(data))
	return j['offlinesplitteduuid']

def show_stats(server, info, player, type, target, isuuid):
	if not isuuid:
		player = name_to_uuid(player)
	jsonfile = worldpath + 'stats/' + player + '.json'
	if not os.isfile(jsonfile):
		server.tell(info.player, errmsg_file)
		return
		
	if not target.startswith('minecraft:'):
		target = 'minecraft:' + target
	if not type.startswith('minecraft:'):
		type = 'minecraft:' + type
		
	with open(jsonfile, "r") as f:
		j = json.load(f)
		try:
			data = j[type][target]
		except KeyError:
			server.tell(info.player, errmsg_target)
			return
			
		str = '该玩家[' + target + ']分类中的[' + target + ']统计信息的值为' + data
		server.tell(info.player, str)

def onServerInfo(server, info):
	command = info.content.split()
	if command[0] != prefix:
		return
	del command[0]
	
	cmdlen = len(command)
	if cmdlen == 0:
		for line in helpmsg.splitlines():
			if info.isPlayer:
				server.tell(info.player, line)
			else:
				print line
		return
	
	isuuid = 0
	if command[cmdlen-1] == '-uuid':
		isuuid = true
		del command[cmdlen-1]
		cmdlen -=1
		
	if cmdlen == 3 and info.isPlayer:
		show_stats(server, info, command[0], command[1], command[2], isuuid)
	else:
		print(errmsg_arg)
