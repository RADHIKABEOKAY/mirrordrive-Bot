from telegram import InlineKeyboardMarkup
from telegram.message import Message
from telegram.update import Update
import psutil, shutil
import time
from bot import AUTO_DELETE_MESSAGE_DURATION, LOGGER, bot, \
    status_reply_dict, status_reply_dict_lock, download_dict, download_dict_lock, botStartTime, Interval, DOWNLOAD_STATUS_UPDATE_INTERVAL
from bot.helper.ext_utils.bot_utils import get_readable_message, get_readable_file_size, get_readable_time, MirrorStatus, setInterval
from telegram.error import TimedOut, BadRequest


def sendMessage(text: str, bot, update: Update):
    try:
        return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, allow_sending_without_reply=True,  parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))
def sendMarkup(text: str, bot, update: Update, reply_markup: InlineKeyboardMarkup):
    return bot.send_message(update.message.chat_id,
                            reply_to_message_id=update.message.message_id,
                            text=text, reply_markup=reply_markup, allow_sending_without_reply=True, parse_mode='HTMl')

def editMessage(text: str, message: Message, reply_markup=None):
    try:
        bot.edit_message_text(text=text, message_id=message.message_id,
                              chat_id=message.chat.id,reply_markup=reply_markup,
                              parse_mode='HTMl')
    except Exception as e:
        LOGGER.error(str(e))


def deleteMessage(bot, message: Message):
    try:
        bot.delete_message(chat_id=message.chat.id,
                           message_id=message.message_id)
    except Exception as e:
        LOGGER.error(str(e))


def sendLogFile(bot, update: Update):
    with open('log.txt', 'rb') as f:
        bot.send_document(document=f, filename=f.name,
                          reply_to_message_id=update.message.message_id,
                          chat_id=update.message.chat_id)


def auto_delete_message(bot, cmd_message: Message, bot_message: Message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(bot, cmd_message)
            deleteMessage(bot, bot_message)
        except AttributeError:
            pass


def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                deleteMessage(bot, message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))


def update_all_messages():
    total, used, free = shutil.disk_usage('.')
    free = get_readable_file_size(free)
    currentTime = get_readable_time(time.time() - botStartTime)
    msg, buttons = get_readable_message()
    msg += f"<b>⌈➳ 🖥 </b> <code>{psutil.cpu_percent()}%</code>" \
           f" <b>⌈ ♻ </b> <code>{psutil.virtual_memory().percent}%</code>" \
           f" <b>| 🧰 : </b> <code>{psutil.disk_usage('/').percent}%</code>"
    with download_dict_lock:
        dlspeed_bytes = 0
        uldl_bytes = 0
        for download in list(download_dict.values()):
            speedy = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if 'K' in speedy:
                    dlspeed_bytes += float(speedy.split('K')[0]) * 1024
                elif 'M' in speedy:
                    dlspeed_bytes += float(speedy.split('M')[0]) * 1048576 
            if download.status() == MirrorStatus.STATUS_UPLOADING:
                if 'KB/s' in speedy:
            	    uldl_bytes += float(speedy.split('K')[0]) * 1024
                elif 'MB/s' in speedy:
                    uldl_bytes += float(speedy.split('M')[0]) * 1048576
        dlspeed = get_readable_file_size(dlspeed_bytes)
        ulspeed = get_readable_file_size(uldl_bytes)
        msg += f"\n<b>⌈➳ 📇 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝚂𝙿𝙰𝙲𝙴 : </b> <code>{free}⊸</code>\n<b>⌈➳ ⏱ 𝙾𝙽𝙻𝙸𝙽𝙴 𝚃𝙸𝙼𝙴 : </b> <code>{currentTime}∾</code>\n<b>⌈➳ ❇️ 𝙸𝙽𝚃𝙴𝚁𝙽𝙴𝚃 𝚂𝙿𝙴𝙴𝙳..! ⇊⇄</b>\n<b>⌈➳ ⏬ DL:</b> <code>{dlspeed}/s</code> 🔻 <b>𖣘︎  ⏫ UL:</b> <code>{ulspeed}/s</code> 🔺\n<b>⌈➳ ✳️ 𝚇-𝚂𝙴𝙴𝙳𝙸𝙽𝙶 : ησηѕтσρ↹Ⓧ</b>\n<b>⌈➳ 🛸 яατιο : </b><code>0.000 ⊹</code>\n<b>⌈➳ 🛅 𝙰𝙱𝙾𝚄𝚃  𝙳𝙰𝚃𝙰 𝚄𝚂𝙰𝙶𝙴 : ↬↧</b>\n<b>⌈➳ 💐 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝙳𝙰𝚃𝙰 : </b> <code>{get_readable_file_size(psutil.net_io_counters().bytes_recv)} ꕳ 🔻</code>\n<b>⌈➳ ☸ 𝚄𝙿𝙻𝙾𝙰𝙳𝙴𝙳 𝙳𝙰𝚃𝙰 : </b> <code>{get_readable_file_size(psutil.net_io_counters().bytes_sent)} ཬ 🔺</code>\n"
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                try:
                    if buttons == "":
                        editMessage(msg, status_reply_dict[chat_id])
                    else:
                        editMessage(msg, status_reply_dict[chat_id], buttons)
                except Exception as e:
                    LOGGER.error(str(e))
                status_reply_dict[chat_id].text = msg


def sendStatusMessage(msg, bot):
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
    total, used, free = shutil.disk_usage('.')
    free = get_readable_file_size(free)
    currentTime = get_readable_time(time.time() - botStartTime)
    progress, buttons = get_readable_message()
    progress += f"<b>⌈➳ 🖥 </b> <code>{psutil.cpu_percent()}%</code>" \
           f" <b> | 🧰 : </b> <code>{psutil.virtual_memory().percent}%</code>" \
           f" <b> | ♻</b> <code>{psutil.disk_usage('/').percent}%</code>"
    with download_dict_lock:
        dlspeed_bytes = 0
        uldl_bytes = 0
        for download in list(download_dict.values()):
            speedy = download.speed()
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if 'K' in speedy:
                    dlspeed_bytes += float(speedy.split('K')[0]) * 1024
                elif 'M' in speedy:
                    dlspeed_bytes += float(speedy.split('M')[0]) * 1048576 
            if download.status() == MirrorStatus.STATUS_UPLOADING:
                if 'KB/s' in speedy:
            	    uldl_bytes += float(speedy.split('K')[0]) * 1024
                elif 'MB/s' in speedy:
                    uldl_bytes += float(speedy.split('M')[0]) * 1048576
        dlspeed = get_readable_file_size(dlspeed_bytes)
        ulspeed = get_readable_file_size(uldl_bytes)
        progress += f"\n<b>⌈➳ 📇 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝚂𝙿𝙰𝙲𝙴 : </b> <code>{free}⊸</code>\n<b>⌈➳ ⏱ 𝙾𝙽𝙻𝙸𝙽𝙴 𝚃𝙸𝙼𝙴 : ∾</b> <code>{currentTime}</code>\n<b>⌈➳ ❇️ 𝙸𝙽𝚃𝙴𝚁𝙽𝙴𝚃 𝚂𝙿𝙴𝙴𝙳..! ⇊⇄</b>\n⌈➳ <b>⏬️ DL :</b> <code>{dlspeed}/s</code> 🔻 <b>𖣘︎  ⏫️️ UL :</b> <code>{ulspeed}/s</code> 🔺\n<b>⌈➳ ✳️ 𝚇-𝚂𝙴𝙴𝙳𝙸𝙽𝙶 : ησηѕтσρ↹Ⓧ</b>\n<b>⌈➳ 🛸 яατιο : </b><code>0.000 ⊹</code>\n<b>⌈➳ 🛅 𝙰𝙱𝙾𝚄𝚃  𝙳𝙰𝚃𝙰 𝚄𝚂𝙰𝙶𝙴 : ↬↧</b>\n<b>⌈➳ 💐 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 𝙳𝙰𝚃𝙰 : </b> <code>{get_readable_file_size(psutil.net_io_counters().bytes_recv)} ꕳ 🔻</code>\n<b>⌈➳ ☸ 𝚄𝙿𝙻𝙾𝙰𝙳𝙴𝙳 𝙳𝙰𝚃𝙰 : </b> <code>{get_readable_file_size(psutil.net_io_counters().bytes_sent)} ཬ 🔺</code>\n"
    with status_reply_dict_lock:
        if msg.message.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.message.chat.id]
                deleteMessage(bot, message)
                del status_reply_dict[msg.message.chat.id]
            except Exception as e:
                LOGGER.error(str(e))
                del status_reply_dict[msg.message.chat.id]
        if buttons == "":
            message = sendMessage(progress, bot, msg)
        else:
            message = sendMarkup(progress, bot, msg, buttons)
        status_reply_dict[msg.message.chat.id] = message
