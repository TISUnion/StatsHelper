StatsHelper
-------

一个统计信息助手的  [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 插件，可查询/排名/使用计分板列出各类统计信息。

适用版本：1.13以上服务器

# 格式说明

`!!stats` 显示帮助信息

`!!stats save` <代名> <统计类别> <统计内容> <标题> 保存一个快速计分板

`!!stats del` <代名> 移除一个快速计分板

`!!stats list` 列出已保存的快速计分板
 
`!!stats query` <玩家> <统计类别> <统计内容> [<-uuid>] [<-tell>]

`!!stats query` <玩家> <代名> [<-uuid>] [<-tell>]

`!!stats rank` <统计类别> <统计内容> (-bot) [<-tell>]

`!!stats rank` <代名> (-bot) [<-tell>]

`!!stats scoreboard` <统计类别> <统计内容> (标题) (-bot)

`!!stats scoreboard` <代名> 显示一个快速计分板

`!!stats scoreboard show` 显示该插件的计分板

`!!stats scoreboard hide` 隐藏该插件的计分板

# 参数说明

<统计类别>: killed, killed_by, dropped, picked_up, used, mined, broken, crafted, custom, killed, killed_by 的 <统计内容> 为 [生物id]

picked_up, used, mined, broken, crafted 的 <统计内容> 为物品/方块id

custom 的 <统计内容> 详见统计信息的json文件，或 [MC Wiki](https://minecraft.fandom.com/zh/wiki/%E7%BB%9F%E8%AE%A1%E4%BF%A1%E6%81%AF)

上述内容无需带minecraft前缀

[<-uuid>]: 用uuid替换玩家名; (-bot): 统计bot与cam; [<-tell>]: 仅自己可见

# 例子

`!!stats save fly custom aviate_one_cm 飞行榜`

`!!stats query Fallen_Breath used water_bucket`

`!!stats rank custom time_since_rest -bot`

`!!stats scoreboard mined stone 挖石榜`
