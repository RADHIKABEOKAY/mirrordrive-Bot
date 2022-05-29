import logging
import re
import threading
import time
import math
import psutil
import shutil
import signal
import subprocess
import os
import asyncio
import requests
import pathlib
import urllib
import string

from bot.helper.telegram_helper.bot_commands import BotCommands
from bot import dispatcher, download_dict, download_dict_lock, STATUS_LIMIT
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from bot.helper.telegram_helper import button_build, message_utils

LOGGER = logging.getLogger(__name__)

MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"

URL_REGEX = r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+"

COUNT = 0
PAGE_NO = 1


class MirrorStatus:
    STATUS_UPLOADING = "⌈➳ ⭐ ⇅𝚄𝚙𝚕𝚘𝚊𝚍𝚒𝚗𝚐.....ꘉ....📤 ⏫ "
    STATUS_DOWNLOADING = "⌈➳ 🌟 ⇅𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍𝚒𝚗𝚐.....ꘉ....📥 ⏬ "
    STATUS_CLONING = " 🤶 Cloning..!. ♻️ "
    STATUS_WAITING = " 😡 𝚆𝚊𝚒𝚝𝚒𝚗𝚐...📝 "
    STATUS_FAILED = " 🧐 Failed 🚫.. Cleaning..🌀"
    STATUS_PAUSE = " 🤷‍♀️ Paused...⏸ "
    STATUS_ARCHIVING = " 💝 Archiving...🔐 "
    STATUS_EXTRACTING = " 💔 Extracting...📂 "
    STATUS_SPLITTING = " 💞 Splitting...✂️ "


PROGRESS_MAX_SIZE = 100 // 8
PROGRESS_INCOMPLETE = ['👑','🎯','🌻', '💍', '👻', '🥀', '💐', '🌹', '💎']

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()

def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'

def getDownloadByGid(gid):
    with download_dict_lock:
        for dl in download_dict.values():
            status = dl.status()
            if (
                status
                not in [
                    MirrorStatus.STATUS_ARCHIVING,
                    MirrorStatus.STATUS_EXTRACTING,
                    MirrorStatus.STATUS_SPLITTING,
                ]
                and dl.gid() == gid
            ):
                return dl
    return None

def getAllDownload():
    with download_dict_lock:
        for dlDetails in download_dict.values():
            status = dlDetails.status()
            if (
                status
                not in [
                    MirrorStatus.STATUS_ARCHIVING,
                    MirrorStatus.STATUS_EXTRACTING,
                    MirrorStatus.STATUS_SPLITTING,
                    MirrorStatus.STATUS_CLONING,
                    MirrorStatus.STATUS_UPLOADING,
                ]
                and dlDetails
            ):
                return dlDetails
    return None

def get_progress_bar_string(status):
    completed = status.processed_bytes() / 8
    total = status.size_raw() / 8
    p = 0 if total == 0 else round(completed * 100 / total)
    p = min(max(p, 0), 100)
    cFull = p // 8
    cPart = p % 8 - 1
    p_str = 'π^' * cFull
    if cPart >= 0:
        p_str += PROGRESS_INCOMPLETE[cPart]
    p_str += ' ' * (PROGRESS_MAX_SIZE - cFull)
    p_str = f"[{p_str}]"
    return p_str

def get_readable_message():
    with download_dict_lock:
        msg = ""
        start = 0
        if STATUS_LIMIT is not None:
            dick_no = len(download_dict)
            global pages
            pages = math.ceil(dick_no/STATUS_LIMIT)
            if PAGE_NO > pages and pages != 0:
                globals()['COUNT'] -= STATUS_LIMIT
                globals()['PAGE_NO'] -= 1
            start = COUNT
        for index, download in enumerate(list(download_dict.values())[start:], start=1):
            msg += f"<b>⌈➳ 🗃 𝙵𝙸𝙻𝙴𝙽𝙰𝙼𝙴 💌 ⪡」: </b> <code>{download.name()} ￫♼</code>"
            msg += f"\n<b>⌈➳ 🔥⇆ 𝚄𝙿𝙳𝙰𝚃𝙴 𝙸𝙽𝙵𝙾 🧐 ⪡」:⌜↬</b>"
            msg += f"\n<b>{download.status()}</b>"
            if download.status() not in [
                MirrorStatus.STATUS_ARCHIVING,
                MirrorStatus.STATUS_EXTRACTING,
                MirrorStatus.STATUS_SPLITTING,
            ]:
                msg += f"\n<code>{get_progress_bar_string(download)} {download.progress()}</code>"
                if download.status() == MirrorStatus.STATUS_CLONING:
                    msg += f"\n<b>ᏟᏞϴΝᎬᎠ :</b> <code>{get_readable_file_size(download.processed_bytes())}</code> of <code>{download.size()}</code>\n<b>⌈➳💧 𝙼𝙸𝚁𝚁𝙾𝚁 𝙲𝙻𝙸𝙴𝙽𝚃 : </b> <code>AutoRclone ⎉</code>"
                elif download.status() == MirrorStatus.STATUS_UPLOADING:
                    msg += f"\n<b>⌈➳ 👰 𝚄𝚙𝚕𝚘𝚊𝚍𝚎𝚍... 💃=> </b> <code>{get_readable_file_size(download.processed_bytes())}</code> of <code>{download.size()}️️️️</code>"
                else:
                    msg += f"\n<b>⌈➳ 👰 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 💃 |</b> <code>{get_readable_file_size(download.processed_bytes())}</code> of <code>{download.size()}</code>"
                msg += f"\n<b>⌈➳ 📯 𝚂𝙿𝙴𝙴𝙳 ⚡ ⪡」:</b> <code>{download.speed()} ⇵</code>"

                msg += f"\n<b>⌈➳ 🕰 𝙴𝚂𝚃𝙸𝙼𝙰𝚃𝙴𝙳 𝚃𝙸𝙼𝙴 ⏳ : </b> <code>{download.eta()}⌛</code>"
                msg += f"\n<b>⌈➳ 😎 𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍𝚎𝚛 | </b> <b>{download.message.from_user.first_name}</b>\n<b>⌈➳ ⚠️ USER - ID ⪡」👉 </b><code>/warn {download.message.from_user.id}</code>"

                try:
                    msg += f"\n<b>⌈➳📡 𝚃𝙾𝚁𝚁𝙴𝙽𝚃 𝙸𝙽𝙵𝙾 ⚓️ ⇒\n⌈➳ 𝚂𝙴𝙴𝙳𝙴𝚁𝚂 🌹: </b> <code>{download.aria_download().num_seeders}</code>" \
                           f" | <b> 𝙿𝙴𝙴𝚁𝚂 🥀 : </b> <code>{download.aria_download().connections}</code>\n<b>⌈➳ 💎 𝙼𝙸𝚁𝚁𝙾𝚁 𝙲𝙻𝙸𝙴𝙽𝚃 |</b> aria2c ◷"
                except:
                    pass
                try:
                    msg += f"\n<b>⌈➳ 🤑 𝚂𝙴𝙴𝙳𝙴𝚁𝚂 : </b> <code>{download.torrent_info().num_seeds}☆</code>" \
                           f"<b>| 𝙻𝙴𝙴𝙲𝙷𝙴𝚁𝚂 :</b> <code>{download.torrent_info().num_leechs}🩸</code>\n<b>⌈➳ 💎 𝚃𝙾𝚁𝚁𝙴𝙽𝚃 𝙲𝙻𝙸𝙴𝙽𝚃 | </b> qBittorrent ¶"
                except:
                    pass
                msg += f"\n<b>⌈➳ 🤷‍♀️ 𝚃𝙾 𝙲𝙰𝙽𝙲𝙴𝙻 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 🤦‍♀️ |</b> \n<b>=> 𝚃𝙾𝙺𝙴𝙽 </b> <code>/{BotCommands.CancelMirror} {download.gid()}</code>"
                msg += f"\n<b> ━━━━━━━━━━━━━━━━━━━━━━━━━━ </b>"
               
                
                
                
            msg += "\n\n"
            if STATUS_LIMIT is not None and index == STATUS_LIMIT:
                break
        if STATUS_LIMIT is not None and dick_no > STATUS_LIMIT:
            msg += f"<b>⌈➳ ⏸ 𝙿𝙰𝙶𝙴  : </b> <code>{PAGE_NO}</code> of <code>{pages}</code> | <b>Tasks 🎀 :</b> <code>{dick_no}</code>\n"
            buttons = button_build.ButtonMaker()
            buttons.sbutton("=> ρяєνιουѕ ⏩ ", "pre")
            buttons.sbutton("=> ղҽxԵ ⏩ ", "nex")
            
            button = InlineKeyboardMarkup(buttons.build_menu(2))
            return msg, button
        return msg, ""

def flip(update, context):
    query = update.callback_query
    query.answer()
    global COUNT, PAGE_NO
    if query.data == "nex":
        if PAGE_NO == pages:
            COUNT = 0
            PAGE_NO = 1
        else:
            COUNT += STATUS_LIMIT
            PAGE_NO += 1
    elif query.data == "pre":
        if PAGE_NO == 1:
            COUNT = STATUS_LIMIT * (pages - 1)
            PAGE_NO = pages
        else:
            COUNT -= STATUS_LIMIT
            PAGE_NO -= 1
    message_utils.update_all_messages()

def check_limit(size, limit, tar_unzip_limit=None, is_tar_ext=False):
    LOGGER.info('🥱Checking File Size...🧐')
    if is_tar_ext and tar_unzip_limit is not None:
        limit = tar_unzip_limit
    if limit is not None:
        limit = limit.split(' ', maxsplit=1)
        limitint = int(limit[0])
        if 'G' in limit[1] or 'g' in limit[1]:
            if size > limitint * 1024**3:
                return True
        elif 'T' in limit[1] or 't' in limit[1]:
            if size > limitint * 1024**4:
                return True

def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result

def is_url(url: str):
    url = re.findall(URL_REGEX, url)
    return bool(url)

def is_gdrive_link(url: str):
    return "drive.google.com" in url

def is_mega_link(url: str):
    return "mega.nz" in url or "mega.co.nz" in url

def get_mega_link_type(url: str):
    if "folder" in url:
        return "folder"
    elif "file" in url:
        return "file"
    elif "/#F!" in url:
        return "folder"
    return "file"

def is_magnet(url: str):
    magnet = re.findall(MAGNET_REGEX, url)
    return bool(magnet)

def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""

    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


next_handler = CallbackQueryHandler(flip, pattern="nex", run_async=True)
previous_handler = CallbackQueryHandler(flip, pattern="pre", run_async=True)
dispatcher.add_handler(next_handler)
dispatcher.add_handler(previous_handler)
