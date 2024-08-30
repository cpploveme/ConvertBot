import re
import yaml
import urllib
import telebot

def load_admin() :
    try :
        with open('./config.yaml', 'r', encoding='utf-8') as f:
            data = yaml.load(stream=f, Loader=yaml.FullLoader)
        return data['admin']
    except :
        pass

def load_token() :
    try :
        with open('./config.yaml', 'r', encoding='utf-8') as f:
            data = yaml.load(stream=f, Loader=yaml.FullLoader)
        return data['token']
    except :
        pass

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

admin_id = load_admin()

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
        bot.reply_to(message, "欢迎使用订阅转换机器人\n\n发送 `/help` 获取帮助\n\n发送 `/convert <订阅链接>` 开始转换操作", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ 出现异常错误", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def start_bot(message):
    try:
        bot.reply_to(message, "发送 `/convert <订阅链接>` 开始转换\n\n发送命令后 选择订阅链接转换后的 `平台 / 格式` 并点击按钮\n\n然后选择 `分流规则` 最后复制 `订阅链接`", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ 出现异常错误", parse_mode='Markdown')

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
            if data.get("airport", None) is not None:
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
    bot.set_my_commands(commands=[telebot.types.BotCommand("help", "帮助菜单"), telebot.types.BotCommand("convert", "订阅转换")])

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

if __name__ == '__main__':
    print('[程序已启动]')
    botinit()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            pass
