import os

Prefix = '!!stats'
PluginName = 'StatsHelper'
ScoreboardName = PluginName
UUIDFile = os.path.join('config', PluginName, 'uuid.json')
UUIDFilePrev = os.path.join('plugins', PluginName, 'uuid.json')
QuickScoreboardFile = os.path.join(
    'config', PluginName, 'quick_scoreboard.json')
ConfigFile = os.path.join('config', PluginName, 'config.json')
RankAmount = 15
rankColor = ['§b', '§d', '§e', '§f']
