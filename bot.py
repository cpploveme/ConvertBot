import re
import yaml
import urllib
import requests
import signal
import sys
import telebot
import time
from urllib.parse import urlparse

admin_id = []

def load_token() :
    try :
        with open('./config.yaml', 'r', encoding='utf-8') as f:
            data = yaml.load(stream=f, Loader=yaml.FullLoader)
        return data['token']
    except :
        pass

# 从 config.yaml 中读取 backend 设置
def load_backend():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        return config.get('backend', None)
    except Exception as e:
        print(f"读取配置文件出错：{e}")
        return None

setbackend = load_backend()

def load_admin_id():
    try:
        with open('./config.yaml', 'r', encoding='utf-8') as f:
            data = yaml.load(stream=f, Loader=yaml.FullLoader)
        return data['admin_id']
    except Exception as e:
        print(f"Error loading admin ID: {e}")
        return None

def load_items() :
    try :
        with open('./config.yaml', 'r', encoding='utf-8') as f:
            data = yaml.load(stream=f, Loader=yaml.FullLoader)
        return int(data['items'])
    except :
        pass

def remove_convert(url):
    if "sub?target=" in url:
        pattern = r"url=([^&]*)"
        match = re.search(pattern, url)
        if match:
            encoded_url = match.group(1)
            decoded_url = urllib.parse.unquote(encoded_url)
            return decoded_url
        else:
            return url
    return url

def get_link(message):
    url_list = re.findall("http[s]?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", message.text)
    temp_list = []
    for url in url_list:
        temp_list.append(remove_convert(url))
    temp_list = list(set(temp_list))
    return temp_list

items_per_page = load_items()

bot = telebot.TeleBot(load_token())
bot_name = ""

@bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
def auto_leave(message):
    if not message.json['new_chat_participant']['username'] in bot_name :
       return
    try :
        if not str(message.from_user.id) in admin_id:
            bot.reply_to(message, "❌ 机器人已启动防拉群模式 请勿拉群呢 ~")
            bot.leave_chat(message.chat.id)
    except :
        pass

@bot.message_handler(commands=['start'])
def start_bot(message):
    try:
        bot.reply_to(message, 
    "🌈 欢迎使用订阅转换机器人\n\n"
    "✨ 发送 `/help` 获取帮助\n"
    "✈ 发送 `/convert <订阅链接>` 开始进行订阅转换操作\n"
    "⚙ 发送 `/backend set <后端链接>` 设置后端地址\n"
    "😥 忘记设置的后端了？发送 `/backend list` 查看后端地址\n"
    "🌏 查看 Web 通讯延迟？找 `/ping` 吧！\n"
    "🔧 需要维护怎么办？`/kill` ME 💀！", 
    parse_mode='Markdown'
)
    except:
        bot.reply_to(message, "❌ 出现异常错误", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def start_bot(message):
    try:
        bot.reply_to(message, "发送 `/convert <订阅链接>` 开始转换\n\n发送命令后 选择订阅链接转换后的 `平台 / 格式` 并点击按钮\n\n然后选择 `分流规则` 最后复制 `订阅链接`", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ 出现异常错误", parse_mode='Markdown')

@bot.message_handler(commands=['backend'])
def backend_handler(message):
    global setbackend
    command_parts = message.text.split()
    if len(command_parts) > 1 and command_parts[1] == 'set':
        if len(command_parts) < 3:
            bot.reply_to(message, "请提供一个完整的后端URL，这样我们才能更换成你的后端哦。使用格式：/backend set <http(s)://域名>")
            return
        new_url = command_parts[2]
        setbackend = None  # 清除旧的后端设置
        bot.reply_to(message, "正在检测后端中...")
        try:
            response = requests.get(f"{new_url}/sub?", verify=False)
            if "Invalid target!" in response.text:
                parsed_url = urlparse(new_url)
                domain = parsed_url.netloc
                setbackend = domain

                # 更新 config.yaml 文件
                with open('config.yaml', 'r', encoding='utf-8') as f:
                    config = yaml.load(f, Loader=yaml.FullLoader)
                config['backend'] = f"{domain}"
                with open('config.yaml', 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True)
                
                bot.reply_to(message, f"域名 {domain} 似乎是一个正确的 Subconvert 后端。\n后端配置存储成功啦")
            else:
                bot.reply_to(message, f"呜呜呜，检测失败了，{new_url} 并不是一个有效的后端。")
        except requests.exceptions.RequestException as e:
            bot.reply_to(message, f"检测失败，无法访问 {new_url}。错误：{e}")
    elif len(command_parts) > 1 and command_parts[1] == 'list':
        if setbackend:
            bot.reply_to(message, f"当前存储的后端域名：{setbackend}")
        else:
            bot.reply_to(message, "当前没有存储任何后端域名。")
    else:
        bot.reply_to(message, "笨蛋！这是一个分支命令！\n使用 /backend set <http(s)://域名> 设置后端\n或者 /backend list 查看已存储的后端。")

@bot.message_handler(commands=['ping'])
def ping_pong(message):
    command_parts = message.text.split()
    if len(command_parts) < 2:
        url = 'https://api.telegram.org'  # 使用 Telegram API 作为默认目标
        target = 'Telegram API'
    else:
        target = command_parts[1]
        url = f'http://{target}'
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5, verify=False)  # 跳过 SSL 证书验证
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        if response.status_code == 200:
            bot.reply_to(message, f"🏓 Ping? Pong! \n✔ 与 {target} 的延迟是：{int(latency)}ms")
        else:
            bot.reply_to(message, f"💣 Ping? Boom! \n❌ 与 {target}连接失败，HTTP 状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"❌ 检测失败，无法 ping 通 {target}。错误：{e}")

@bot.message_handler(commands=['convert'])
def convert_sub(message):
    try:
        if not message.chat.type == "private" :
            bot.reply_to(message, f"❌ 请私聊使用本机器人呢 ~", parse_mode='Markdown')
            return
        with open('./config.yaml', 'r', encoding='utf-8') as f:
            data = yaml.load(stream=f, Loader=yaml.FullLoader)
            
        url_list = get_link(message)
        if len(url_list) == 0:
            bot.reply_to(message, "您转换的内容不包含 `订阅链接` 呢 ~", parse_mode='Markdown')
            return
        try:
            for url in url_list:
                flag = False
                for airport in data["airport"]:
                    if urllib.parse.urlparse(url).netloc == airport:
                        flag = True
                    if urllib.parse.urlparse(url).netloc == urllib.parse.urlparse(airport).netloc:
                        flag = True
                if flag == False:
                    bot.reply_to(message, f"❌ 不支持转换订阅域名 `{urllib.parse.urlparse(url).netloc}` 呢 ~", parse_mode='Markdown')
                    return
        except:
            pass
        keyboard = []
        i = 0
        page_buttons = []
        if len(data['platform']) % items_per_page > 0:
            pages = len(data['platform']) // items_per_page + 1
        else:
            pages = len(data['platform']) // items_per_page
        for platform in data['platform']:
            if i > items_per_page:
                break
            i = i + 1
            if i % 2 == 1:
                page_buttons = []
                temp_button = telebot.types.InlineKeyboardButton(f'{platform}', callback_data=f'platform {platform}')
                page_buttons.append(temp_button)
            else :
                temp_button = telebot.types.InlineKeyboardButton(f'{platform}', callback_data=f'platform {platform}')
                page_buttons.append(temp_button)
                keyboard.append(page_buttons)
        page_info = f'{1} / {pages}'
        prev_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
        if pages == 1 : 
            next_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
        else :
            next_button = telebot.types.InlineKeyboardButton('下一页', callback_data='platform next 1')
        page_button = telebot.types.InlineKeyboardButton(page_info, callback_data=f'page_info {1} {pages}')
        page_buttons = [prev_button, page_button, next_button]
        keyboard.append(page_buttons)
        keyboard.append([telebot.types.InlineKeyboardButton('关闭', callback_data='close')])
        reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
        bot.reply_to(message, "请选择 `生成类型` :", parse_mode='Markdown', reply_markup=reply_markup)
    except:
        bot.reply_to(message, "❌ 出现异常错误", parse_mode='Markdown')

def botinit():
    global bot_name
    bot_name = '@' + bot.get_me().username
    bot.delete_my_commands(scope=None, language_code=None)
    bot.polling(none_stop=True)
    bot.set_my_commands(commands=[telebot.types.BotCommand("start", "开始"), telebot.types.BotCommand("help", "主要命令帮助菜单"), telebot.types.BotCommand("convert", "订阅转换"), telebot.types.BotCommand("ping", "web延迟测试"), telebot.types.BotCommand("kill", "KILL ME")])

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        command_type = call.data.split()[0]
        if command_type == "platform":
            op = call.data.split()[1]
            if op == "next":
                current_page = int(call.data.split()[2]) + 1

                with open('./config.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                keyboard = []
                i = 0
                page_buttons = []
                if len(data['platform']) % items_per_page > 0:
                    pages = len(data['platform']) // items_per_page + 1
                else:
                    pages = len(data['platform']) // items_per_page
                for platform in data['platform']:
                    if i < (current_page - 1) * items_per_page:
                        i = i + 1
                        continue
                    if i > items_per_page * current_page:
                        break
                    i = i + 1
                    if i % 2 == 1:
                        page_buttons = []
                        temp_button = telebot.types.InlineKeyboardButton(f'{platform}', callback_data=f'platform {platform}')
                        page_buttons.append(temp_button)
                    else :
                        temp_button = telebot.types.InlineKeyboardButton(f'{platform}', callback_data=f'platform {platform}')
                        page_buttons.append(temp_button)
                        keyboard.append(page_buttons)
                page_info = f'{current_page} / {pages}'
                if current_page == 1:
                    prev_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else:
                    prev_button = telebot.types.InlineKeyboardButton('上一页', callback_data=f'platform prev {current_page}')
                if current_page == pages : 
                    next_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else :
                    next_button = telebot.types.InlineKeyboardButton('下一页', callback_data=f'platform next {current_page}')
                page_button = telebot.types.InlineKeyboardButton(page_info, callback_data=f'page_info {current_page} {pages}')
                page_buttons = [prev_button, page_button, next_button]
                keyboard.append(page_buttons)
                keyboard.append([telebot.types.InlineKeyboardButton('关闭', callback_data='close')])
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="请选择 `生成类型` :", parse_mode='Markdown', reply_markup=reply_markup)
            elif op == "prev":
                current_page = int(call.data.split()[2]) - 1

                with open('./config.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                keyboard = []
                i = 0
                page_buttons = []
                if len(data['platform']) % items_per_page > 0:
                    pages = len(data['platform']) // items_per_page + 1
                else:
                    pages = len(data['platform']) // items_per_page
                for platform in data['platform']:
                    if i < (current_page - 1) * items_per_page:
                        i = i + 1
                        continue
                    if i > items_per_page * current_page:
                        break
                    i = i + 1
                    if i % 2 == 1:
                        page_buttons = []
                        temp_button = telebot.types.InlineKeyboardButton(f'{platform}', callback_data=f'platform {platform}')
                        page_buttons.append(temp_button)
                    else :
                        temp_button = telebot.types.InlineKeyboardButton(f'{platform}', callback_data=f'platform {platform}')
                        page_buttons.append(temp_button)
                        keyboard.append(page_buttons)
                page_info = f'{current_page} / {pages}'
                if current_page == 1:
                    prev_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else:
                    prev_button = telebot.types.InlineKeyboardButton('上一页', callback_data=f'platform prev {current_page}')
                if current_page == pages : 
                    next_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else :
                    next_button = telebot.types.InlineKeyboardButton('下一页', callback_data=f'platform next {current_page}')
                page_button = telebot.types.InlineKeyboardButton(page_info, callback_data=f'page_info {current_page} {pages}')
                page_buttons = [prev_button, page_button, next_button]
                keyboard.append(page_buttons)
                keyboard.append([telebot.types.InlineKeyboardButton('关闭', callback_data='close')])
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="请选择 `生成类型` :", parse_mode='Markdown', reply_markup=reply_markup)
            else :
                with open('./config.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                keyboard = []
                i = 0
                page_buttons = []
                if len(data['rule']) % items_per_page > 0:
                    pages = len(data['rule']) // items_per_page + 1
                else:
                    pages = len(data['rule']) // items_per_page
                ptf = call.data.split()[1]
                for rule in data['rule']:
                    if i > items_per_page:
                        break
                    i = i + 1
                    if i % 2 == 1:
                        page_buttons = []
                        temp_button = telebot.types.InlineKeyboardButton(f'{rule}', callback_data=f'rule {rule} {ptf}')
                        page_buttons.append(temp_button)
                    else :
                        temp_button = telebot.types.InlineKeyboardButton(f'{rule}', callback_data=f'rule {rule} {ptf}')
                        page_buttons.append(temp_button)
                        keyboard.append(page_buttons)
                page_info = f'{1} / {pages}'
                prev_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                if pages == 1 : 
                    next_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else :
                    next_button = telebot.types.InlineKeyboardButton('下一页', callback_data=f'rule next 1 {ptf}')
                page_button = telebot.types.InlineKeyboardButton(page_info, callback_data=f'page_info {1} {pages}')
                page_buttons = [prev_button, page_button, next_button]
                keyboard.append(page_buttons)
                keyboard.append([telebot.types.InlineKeyboardButton('关闭', callback_data='close')])
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="请选择 `规则` :", parse_mode='Markdown', reply_markup=reply_markup)
        elif command_type == "rule":
            op = call.data.split()[1]
            if op == "next":
                current_page = int(call.data.split()[2]) + 1

                with open('./config.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                keyboard = []
                i = 0
                page_buttons = []
                if len(data['rule']) % items_per_page > 0:
                    pages = len(data['rule']) // items_per_page + 1
                else:
                    pages = len(data['rule']) // items_per_page
                for rule in data['rule']:
                    if i < (current_page - 1) * items_per_page:
                        i = i + 1
                        continue
                    if i > items_per_page * current_page:
                        break
                    i = i + 1
                    if i % 2 == 1:
                        page_buttons = []
                        temp_button = telebot.types.InlineKeyboardButton(f'{rule}', callback_data=f'rule {rule} {call.data.split()[3]}')
                        page_buttons.append(temp_button)
                    else :
                        temp_button = telebot.types.InlineKeyboardButton(f'{rule}', callback_data=f'rule {rule} {call.data.split()[3]}')
                        page_buttons.append(temp_button)
                        keyboard.append(page_buttons)
                page_info = f'{current_page} / {pages}'
                if current_page == 1:
                    prev_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else:
                    prev_button = telebot.types.InlineKeyboardButton('上一页', callback_data=f'rule prev {current_page} {call.data.split()[3]}')
                if current_page == pages : 
                    next_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else :
                    next_button = telebot.types.InlineKeyboardButton('下一页', callback_data=f'rule next {current_page} {call.data.split()[3]}')
                page_button = telebot.types.InlineKeyboardButton(page_info, callback_data=f'page_info {current_page} {pages} {call.data.split()[3]}')
                page_buttons = [prev_button, page_button, next_button]
                keyboard.append(page_buttons)
                keyboard.append([telebot.types.InlineKeyboardButton('关闭', callback_data='close')])
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="请选择 `规则` :", parse_mode='Markdown', reply_markup=reply_markup)
            elif op == "prev":
                current_page = int(call.data.split()[2]) - 1

                with open('./config.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                keyboard = []
                i = 0
                page_buttons = []
                if len(data['rule']) % items_per_page > 0:
                    pages = len(data['rule']) // items_per_page + 1
                else:
                    pages = len(data['rule']) // items_per_page
                for rule in data['rule']:
                    if i < (current_page - 1) * items_per_page:
                        i = i + 1
                        continue
                    if i > items_per_page * current_page:
                        break
                    i = i + 1
                    if i % 2 == 1:
                        page_buttons = []
                        temp_button = telebot.types.InlineKeyboardButton(f'{rule}', callback_data=f'rule {rule} {call.data.split()[3]}')
                        page_buttons.append(temp_button)
                    else :
                        temp_button = telebot.types.InlineKeyboardButton(f'{rule}', callback_data=f'rule {rule} {call.data.split()[3]}')
                        page_buttons.append(temp_button)
                        keyboard.append(page_buttons)
                page_info = f'{current_page} / {pages}'
                if current_page == 1:
                    prev_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else:
                    prev_button = telebot.types.InlineKeyboardButton('上一页', callback_data=f'rule prev {current_page} {call.data.split()[3]}')
                if current_page == pages : 
                    next_button = telebot.types.InlineKeyboardButton('      ', callback_data='blank')
                else :
                    next_button = telebot.types.InlineKeyboardButton('下一页', callback_data=f'rule next {current_page} {call.data.split()[3]}')
                page_button = telebot.types.InlineKeyboardButton(page_info, callback_data=f'page_info {current_page} {pages} {call.data.split()[3]}')
                page_buttons = [prev_button, page_button, next_button]
                keyboard.append(page_buttons)
                keyboard.append([telebot.types.InlineKeyboardButton('关闭', callback_data='close')])
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="请选择 `规则` :", parse_mode='Markdown', reply_markup=reply_markup)
            else :
                with open('./config.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.load(stream=f, Loader=yaml.FullLoader)
                url_list = get_link(call.message.reply_to_message)
                backend = data['backend']
                if not "http" in backend:
                    backend = "https://" + backend
                backend = urllib.parse.urlparse(backend).netloc
                result = "https://"+ backend + "/sub?target=" + str(data['platform'][str(call.data.split()[2])]) + "&url=" + urllib.parse.quote_plus(url_list[0])
                for url in url_list[1:]:
                    if len(url) != 0:
                        result = result + "|" + urllib.parse.quote_plus(url)
                result = result + "&config=" + str(data['rule'][str(call.data.split()[1])]) + str(data['parameter'])
                keyboard = []
                reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"点击以下链接复制到软件内订阅即可 ~\n\n`{result}`", parse_mode='Markdown', reply_markup=reply_markup)
        elif command_type == "page_info":
            bot.answer_callback_query(call.id, f"第 {call.data.split()[1]} 页  共 {call.data.split()[2]} 页", show_alert=True)
        elif command_type == "close":
            bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        keyboard = []
        reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ 出现异常错误", parse_mode='Markdown', reply_markup=reply_markup)

def signal_handler(sig, frame):
    print('正在停止 bot...')
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

shutdown_flag = False

@bot.message_handler(commands=['kill'])
def killme_command(message):
    global shutdown_flag
    ADMIN_ID = load_admin_id()
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "💀 Bot 即将关闭...")
        shutdown_flag = True
        bot.stop_polling()  # 停止 polling
        sys.exit(0)  # 正常退出程序
    else:
        bot.reply_to(message, "❌ 你没有权限执行这个命令。")

if __name__ == '__main__':
    print('[程序已启动]')
    while not shutdown_flag:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"发生异常: {e}")
            time.sleep(5)  # 出现异常后等待 5 秒后重启轮询
