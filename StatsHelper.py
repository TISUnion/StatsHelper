# -*- coding: utf-8 -*-

import json
import os
import urllib2
import time

ServerPath = 'server/'
WorldPath = ServerPath + 'world/'
Prefix = '!!stats'
ScoreboardName = 'StatsHelper'
DebugOutput = 0
RankAmount = 15
HelpMessage = '''------MCD StatsHelper插件 v2.0------
一个统计信息助手插件，可查询/排名/使用计分板列出各类统计信息。
§a【格式说明】§r
§7''' + Prefix + '''§r 显示帮助信息
§7''' + Prefix + ''' query §b[玩家] §6[统计类别] §e[统计内容] §7(-uuid)§r §7(-tell)§r
§7''' + Prefix + ''' rank §6[统计类别] §e[统计内容] §7(-bot)§r §7(-tell)§r
§7''' + Prefix + ''' scoreboard §6[统计类别] §e[统计内容] §7(-bot)§r
§7''' + Prefix + ''' scoreboard show§r 显示该插件的计分板
§7''' + Prefix + ''' scoreboard hide§r 隐藏该插件的计分板
§a【参数说明】§r
§6[统计类别]§r: §6killed§r, §6killed_by§r, §6dropped§r, §6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r, §6custom§r
§6killed§r, §6killed_by§r 的 §e[统计内容] §r为 §e[生物id]§r
§6picked_up§r, §6used§r, §6mined§r, §6broken§r, §6crafted§r 的 §e[统计内容]§r 为 §e[物品/方块id]§r
§6custom§r 的 §e[统计内容]§r 详见统计信息的json文件
上述内容无需带minecraft前缀
§7(-uuid)§r: 用uuid替换玩家名; §7(-bot)§r: 统计bot与cam; §7(-tell)§r: 仅自己可见
§a【例子】§r
§7''' + Prefix + ''' query §bFallen_Breath §6used §ewater_bucket§r
§7''' + Prefix + ''' rank §6custom §etime_since_rest §7-bot§r
§7''' + Prefix + ''' scoreboard §6mined §estone§r
'''

def DebugPrint(server, info, msg):
	if DebugOutput:
		printMessage(server, info, '[StatsHelper]' + msg)
		
def DebugPrintList(server, info, msg, lst):
	if DebugOutput:
		DebugPrint(server, info, msg)
		for i in lst:
			DebugPrint(server, info, '    ' + i)
			
def name_to_uuid_fromAPI(name):
	url = 'http://tools.glowingmines.eu/convertor/nick/' + name
	response = urllib2.urlopen(url)
	data = response.read()
	js = json.loads(str(data))
	return js['offlinesplitteduuid']
	
def name_to_uuid(server, info, name):
	fileName = ServerPath + 'usercache.json'
	if os.path.isfile(fileName):
		with open(fileName, 'r') as f:
			try:
				js = json.load(f)
			except ValueError:
				printMessage(server, info, 'cann\'t open json file '+fileName)
				return name_to_uuid_fromAPI(name)
			for i in js:
				if i['name'] == name:
					return i['uuid']
	printMessage(server, info, 'name not found, use API')
	return name_to_uuid_fromAPI(name)

def isBot(name):
	blacklist = 'A_Pi#nw#sw#SE#ne#nf#SandWall#storage#zi_ming#Steve#Alex###########'
	blackkey = ['farm', 'bot_', 'cam', '_b_', 'bot-']
	if blacklist.find(name) >= 0: return True
	if len(name) <= 4 or len(name) > 16: return True
	for i in blackkey:
		if name.find(i) >= 0:
			return True
	return False

def printMessage(server, info, msg, isTell = True):
	for line in msg.splitlines():
		if info.isPlayer:
			if isTell:
				server.tell(info.player, line)
			else:
				server.say(line)
		else:
			print line
			
def getData(server, info, uuid, classification, target):
	jsonfile = WorldPath + 'stats/' + uuid + '.json'
	if not os.path.isfile(jsonfile):
		#printMessage(server, info, '未找到该玩家的统计文件！')
		return (0, False)
		
	with open(jsonfile, 'r') as f:
		try:
			DebugPrint(server, info, 'trying to read ' + jsonfile)
			js = json.load(f)
		except ValueError:
			#printMessage(server, info, '统计文件读取失败')
			return (0, False)
		try:
			data = js['stats']['minecraft:' + classification]['minecraft:' + target]
		except KeyError:
			#printMessage(server, info, '未找到该统计项！')
			return (0, False)
		return (data, True)
		
def getPlayerList(server, info, listBot):
	fileName = ServerPath + 'usercache.json'
	ret = []
	flag = False
	if os.path.isfile(fileName):
		with open(fileName, 'r') as f:
			try:
				js = json.load(f)
			except ValueError:
				#printMessage(server, info, 'cann\'t open json file ' + fileName)
				return (ret, False)
			for i in js:
				name = i['name']
				if not listBot and isBot(name):
					continue
				ret.append((name, i['uuid']))
		flag = True
	else:
		printMessage(server, info, 'usercache.json not found')
	return (ret, flag)
	
def triggerSaveAll(server):
	server.execute('save-all')
	time.sleep(0.2)

def showStats(server, info, name, classification, target, isUUID, isTell):
	uuid = name
	if not isUUID:
		uuid = name_to_uuid(server, info, uuid)
	DebugPrint(server, info, 'uuid = ' + uuid)
	
	data = getData(server, info, uuid, classification, target)
	
	msg = '玩家§b' + name + '§r的统计信息[§6' + classification + '§r.§e' + target + '§r]的值为§a' + str(data) + '§r'
	printMessage(server, info, msg, isTell)
		
def showRank(server, info, classification, target, listBot, isTell):
	getPlayerListResult = getPlayerList(server, info, listBot)
	if getPlayerListResult[1]:
		arr = []
		for player in getPlayerListResult[0]:
			ret = getData(server, info, player[1], classification, target)
			if ret[1] and ret[0] >= 0:
				data = ret[0]
				if DebugOutput > 1: DebugPrint(server, info, 'append [' + name + ', ' + str(data) + ']')
				arr.append((player[0], data))
	
		if len(arr) == 0:
			printMessage(server, info, '未找到该统计项或该统计项全空！')
			return
		arr.sort(key = lambda x:x[0])
		arr.reverse()
		arr.sort(key = lambda x:x[1])
		arr.reverse()
		
		printMessage(server, info, '统计信息[§6' + classification + '§r.§e' + target + '§r]的前十五名为', isTell)
		maxnamelen = 0
		for i in range(0, min(RankAmount, len(arr))):
			maxnamelen = max(maxnamelen, len(str(arr[i][1])))
		for i in range(0, min(RankAmount, len(arr))):
			printMessage(server, info, '#' + str(i + 1) + ' ' * (3-len(str(i + 1))) + str(arr[i][1]) + ' ' * (maxnamelen - len(str(arr[i][1])) + 1) + arr[i][0], isTell)
	else:
		printMessage(server, info, '玩家列表读取失败')

def showScoreboard(server, info):
	server.execute('scoreboard objectives setdisplay sidebar ' + ScoreboardName)

def hideScoreboard(server, info):
	server.execute('scoreboard objectives setdisplay sidebar')
	
def buildScoreboard(server, info, classification, target, listBot):
	getPlayerListResult = getPlayerList(server, info, listBot)
	if getPlayerListResult[1]:
		triggerSaveAll(server)
		server.execute('scoreboard objectives remove ' + ScoreboardName)
		server.execute('scoreboard objectives add ' + ScoreboardName + ' ' +
			'minecraft.' + classification + ':minecraft.' + target + 
			' {"text":"§6' + classification + '§r.§e' + target + '"}')
		for player in getPlayerListResult[0]:
			ret = getData(server, info, player[1], classification, target)
			if ret[1]:
				server.execute('scoreboard players set ' + player[0] + ' ' + ScoreboardName + ' ' + str(ret[0]))
		showScoreboard(server, info)
	else:
		printMessage(server, info, '玩家列表读取失败')
		
def onServerInfo(server, info):
	content = info.content
	isUUID = content.find('-uuid') >= 0
	content = content.replace('-uuid', '')
	listBot = content.find('-bot') >= 0
	content = content.replace('-bot', '')
	isTell = content.find('-tell') >= 0
	content = content.replace('-tell', '')
	if not info.isPlayer and content.endswith('<--[HERE]'):
		content = content.replace('<--[HERE]', '')
		
	command = content.split()
	if command[0] != Prefix:
		return
	DebugPrint(server, info, 'raw content = ' + info.content)
	DebugPrintList(server, info, 'raw command = ' , command)
	del command[0]
	
	if len(command) == 0:
		printMessage(server, info, HelpMessage)
		return
	
	
	cmdlen = len(command)
	DebugPrintList(server, info, 'processed command = ', command)
	DebugPrint(server, info, '[isUUID, listBot] = [' + str(isUUID) + ', ' + str(listBot) + ']')
	# query [玩家] [统计类别] [统计内容] (-uuid)
	if cmdlen == 4 and command[0] == 'query':
		showStats(server, info, command[1], command[2], command[3], isUUID, isTell)
	# rank [统计类别] [统计内容] (过滤bot前缀)
	elif cmdlen == 3 and command[0] == 'rank':
		showRank(server, info, command[1], command[2], listBot, isTell)
	elif cmdlen == 3 and command[0] == 'scoreboard':
		buildScoreboard(server, info, command[1], command[2], listBot)
	elif cmdlen == 2 and command[0] == 'scoreboard' and command[1] == 'show':
		showScoreboard(server, info)
	elif cmdlen == 2 and command[0] == 'scoreboard' and command[1] == 'hide':
		hideScoreboard(server, info)
	else:
		printMessage(server, info, '参数错误！请输入'+Prefix+'以获取插件帮助')
