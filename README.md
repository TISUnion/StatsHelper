StatsHelper
-------

一个统计信息助手的  [MCDReforged](https://github.com/Fallen-Breath/MCDReforged) 插件，可查询/排名/使用计分板列出各类统计信息。

适用版本：1.13以上服务器

# 格式说明

`!!stats` 显示帮助信息

`!!stats` <代名> 快速显示一个保存的排行榜

`!!stats save` <代名> <统计类别> <统计内容> <标题> 保存一个计分项到快速访问

`!!stats del` <代名> 移除一个快速访问中的计分项

`!!stats list` 列出已保存的快速访问计分项
 
`!!stats query` <玩家> <统计类别> <统计内容> [<-uuid>] [<-tell>]

`!!stats rank` <统计类别> <统计内容> (-bot) [<-tell>]

`!!stats scoreboard` <统计类别> <统计内容> (标题) (-bot)

`!!stats scoreboard show` 显示该插件的计分板

`!!stats scoreboard hide` 隐藏该插件的计分板

# 参数说明
<代名>: 可以使用`!!stats list`来查阅, 此外`!!stats query/rank`中的<统计类别> <统计内容>也可使用<代名>来替代

<统计类别>: killed, killed_by, dropped, picked_up, used, mined, broken, crafted, custom, killed, killed_by 的 <统计内容> 为 [生物id]

picked_up, used, mined, broken, crafted 的 <统计内容> 为物品/方块id

custom 的 <统计内容> 详见统计信息的json文件

上述内容无需带minecraft前缀

[<-uuid>]: 用uuid替换玩家名; (-bot): 统计bot与cam; [<-tell>]: 仅自己可见

# 例子
`!!stats save fly custom aviate_one_cm 飞行榜`

`!!stats query Fallen_Breath used water_bucket`

`!!stats rank custom time_since_rest -bot`

`!!stats scoreboard mined stone 挖石榜`
