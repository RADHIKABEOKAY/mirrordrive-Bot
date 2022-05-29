import subprocess
from bot import LOGGER, dispatcher
from telegram import ParseMode
from telegram.ext import CommandHandler
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands


def shell(update, context):
    message = update.effective_message
    cmd = message.text.split(' ', 1)
    if len(cmd) == 1:
        message.reply_text('=> Bye Dear..! 😎')
        return
    cmd = cmd[1]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    reply = ''
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        reply += f"*=> Root update Info..!*\n️=>️\n️\n`{stdout}`\n️️\n"
        LOGGER.info(f"Shell - {cmd} - {stdout}")
    if stderr:
        reply += f"*=> U Idiot.. Don't Do it again..!*\n️=>️\n️\n`{stderr}`\n"
        LOGGER.error(f"Shell - {cmd} - {stderr}")
    if len(reply) > 3000:
        with open('️Terminal_output.xml', 'w') as file:
            file.write(reply)
        with open('️Terminal_output.xml', 'rb') as doc:
            context.bot.send_document(
                document=doc,
                filename=doc.name,
                reply_to_message_id=message.message_id,
                chat_id=message.chat_id)
    else:
        message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


SHELL_HANDLER = CommandHandler(BotCommands.ShellCommand, shell,

filters=CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(SHELL_HANDLER)
