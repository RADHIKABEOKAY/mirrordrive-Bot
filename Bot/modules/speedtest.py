from speedtest import Speedtest
from bot.helper.telegram_helper.filters import CustomFilters
from bot import dispatcher
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from telegram.ext import CommandHandler


def speedtest(update, context):
    speed = sendMessage("🤣 𝚁𝚄𝙽𝙽𝙸𝙽𝙶 𝚂𝙿𝙴𝙴𝙳 𝚃𝙴𝚂𝚃..⚡ ", context.bot, update)
    test = Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()
    string_speed = f'''
<b> 🎀 𝚂𝙴𝚁𝚅𝙴𝚁 📌</b>
<b>🌟 𝙽𝙰𝙼𝙴 ✅  : </b> <code>{result['server']['name']} ☠️</code>
<b>🛠 𝙲𝙾𝚄𝙽𝚃𝚁𝚈 🌐 : </b> <code>{result['server']['country']} 🇮🇳, {result['server']['cc']}</code>
<b>💐 @Mirrordrive 💝 : </b> <code>{result['server']['sponsor']} 💀</code>
<b>🔥 𝙸𝚂𝙿-5𝙶 📶 : </b> <code>{result['client']['isp']}</code>\n<b>💎 ɓყ ⋍ 🅅🄸</b>

<b>💘 𝚂𝙿𝙴𝙴𝙳 𝚃𝙴𝚂𝚃 𝚁𝙴𝚂𝚄𝙻𝚃𝚂.. 🥳</b>
<b>⏫ 𝚄𝙿𝙻𝙾𝙰𝙳 💓 : </b> <code>{speed_convert(result['upload'] / 8)}</code>
<b>⏬ 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳 💞 : </b>  <code>{speed_convert(result['download'] / 8)}</code>
<b>😤 𝙿𝙸𝙽𝙶 💢 : </b> <code>{result['ping']} 𝙼𝚂 🎯 </code>
<b>🥱 𝙸𝚂𝙿 𝙻𝙾𝙻 ♐ : </b> <code>{result['client']['isprating']} 💃</code>
'''"<a href='https://telegra.ph/file/b02788a8c2c7ca546d369.jpg'>️</a>"
    editMessage(string_speed, speed)


def speed_convert(size):
    """Hi human, you can't read bytes?"""
    power = 2 ** 10
    zero = 0
    units = {0: "", 1: "Kb/s", 2: "MB/s", 3: "Gb/s", 4: "Tb/s"}
    while size > power:
        size /= power
        zero += 1
    return f"{round(size, 2)} {units[zero]}"


SPEED_HANDLER = CommandHandler(BotCommands.SpeedCommand, speedtest, 
                                                  filters= CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)

dispatcher.add_handler(SPEED_HANDLER)
