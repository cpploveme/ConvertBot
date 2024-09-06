（总结：你开源啊我开源，大家一起蛋的闲）

# 订阅转换Bot

订阅转换Bot是一个基于 `Telegram Api` 的订阅转换前端，可以方便地选择转换目标类型和规则来生成订阅转换链接。

该项目由Poxei DOON大佬提供原始版本，现在、Poxei Doon放弃维护代码，增加功能，由我来进行这个仓库的代码更新，维护

## 关于数据安全

订阅转换 Bot 处理的所有的数据均已公开开源，项目所有的代码操作除与telegram官方dc服务器通讯，和与自己的后端链接，ping命令网页加载外，您的订阅都不会以任何方式保存

订阅链接仅会进行编码和拼接，不会保存

## 机器人安装方法

### 搭建

> 这里以 `Debian` 系统为例

你首先可能需要安装软件包

```bash
apt install git python3-pip -y
```

然后拉取项目

```bash
git clone https://github.com/cpploveme/ConvertBot.git
```

安装依赖

```bash
pip install re pyyaml telebot
```

> 对于高版本且非虚拟环境搭建的Bot你可能需要加上 `--break-system-packages`

关于如何让 Bot 持久化运行这里不会详细说，你可以参考 `screen`, `pm2`, `systemd` 等方法，这里提供一个使用 `screen` 的简单进程守护方式。

```bash
cd ConvertBot
apt install screen -y
screen -R convertbot
python3 bot.py
```

### 机器人配置说明

#### 必要配置

`token`：不填入则 Bot 无法启动，`Bot Token` 可以在 `@BotFather` 获取。

`admin`：不填入则 Bot 无法由您拉入群聊内，但仍仅可在私聊内使用以防暴露订阅链接。

`items`：不填入则 Bot 按钮无法生成。

#### 可选配置

建议参看 `readme.config.yaml` 内的详细说明，也可以使用 `example.config.yaml` 的样例配置。

需要注意的是，`规则名称` 和 `平台名称` 不要包含空格，也不要太长，因为要作为按钮的文本和回调数据，过长可能会导致按钮无法生成。

`airport` 配置如若不填或者直接删去即为不限制订阅转换的链接。

## 机器人使用方法

> 请注意 Bot 命令仅可在私聊中使用

我的分支，包含了原版项目的内容，还对此有其他的更新

#### /start

更清楚的帮助菜单

#### /help

获取基础命令帮助菜单

#### /convert <订阅链接>

发送命令转换订阅链接后，选择需要转换的类型和订阅规则即可生成订阅链接。

#### /kill

杀死bot进程（也在运行过程中适配ctrl + c退出操作，效果同理）

#### /ping <网站url，后端url等：非必须>

如果不填写网页url：对 telegram官方api服务器 测试真连接延迟

如果填写网页url：对该 网页url 测试真连接延迟

#### /backend set <subconvert后端url>

检测backend合规性，更换backend后端，并影响convert转换url

#### /backend list

查看设置的subconvert后端url
