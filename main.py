#!/bin/python
# Async management:
import asyncio

# Telegram API:
import telepot
from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import pave_event_space, per_chat_id, create_open

# For equation processing:
import pyparsing
from eq_parse import *

# URL Processing:
from link_manager import *

# File management and shell interaction:
from shutil import copyfile
import os
import subprocess

# File used to store tokens and paths off of git
from secret import *


functionality_rundown = """Current functionality: 
•Send a url to have it downloaded and sent back
•/calc [expression] evaluates basic expressions
•>> has the same functionality as calc
•[IN PROGRESS] Send a .torrent file to have it's file downloaded and sent back

/help to review this list at any time
"""


def clean_file(file):
    name = file.name
    file.close()
    os.remove(name)


class MessageHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(MessageHandler, self).__init__(*args, **kwargs)
        self._count = 0

    async def on_chat_message(self, msg):
        self._count += 1
        content_type, chat_type, chat_id = telepot.glance(msg)  # Pull possibly useful info

        """
        # Debug message
        await self.sender.sendMessage('Message ' + str(self._count) + ' in current session.' + '\nType:' + content_type)
        """

        """
        # Example of sending a file from the project file 
        with open('test.txt', 'rb') as f:
            await self.sender.sendDocument(f)
        """

        if content_type == 'text':  # If message contains text -----------------------------------------------
            # Help or start commands
            if msg['text'][0:6] == '/start' or msg['text'][0:5] == '/help':
                await self.sender.sendMessage('Welcome to Pi Bot. \n\n' + functionality_rundown)
                return

            # Basic calculations with /calc
            if msg['text'][0:5] == '/calc' or msg['text'][0:2] == '>>':
                in_str = msg['text'].replace('/calc', '')
                in_str = in_str.replace('>>', '')

                nsp = NumericStringParser()
                try:
                    result = nsp.eval(in_str)
                except pyparsing.ParseException:
                    print('Expression processing failed.')
                    await self.sender.sendMessage('Invalid equation. \n\n' + functionality_rundown)
                    return
                print('Expression processed.')
                await self.sender.sendMessage(result)
                del nsp
                return

            # Roll for a number with /roll or roll
            if msg['text'][0:5] == '/roll' or msg['text'][0:4].lower() == 'roll':
                in_str = msg['text'].replace('/', '').lower()
                in_str = in_str.replace('roll', '')

                try:
                    in_num = int(in_str)
                    rand_int = rng.randint(1, in_num)
                except ValueError:
                    print('Roll failed.')
                    await self.sender.sendMessage(
                        'Invalid roll, format is /roll [integer]. \n\n' + functionality_rundown)
                    return

                print('Successful roll.')
                await self.sender.sendMessage('Roll 1 to %d: %d' % (in_num, rand_int))
                return

            # Restart Pi command
            if msg['text'][0:2] == '//':
                cmd = msg['text'][2:]
                await self.sender.sendMessage('Executing command: ' + cmd)
                result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
                strOut = result.stdout.decode('UTF-8')
                await self.sender.sendMessage(strOut)
                print('Command executed: ' + cmd)
                return

            # Handling of magnet links:
            if msg['text'][0:7] == 'magnet:':
                await self.sender.sendMessage('Magnet links are not supported yet. \n\n' + functionality_rundown)
                return

            # Processing file downloads from links:
            print('URL received...')
            await self.sender.sendMessage('URL received.')
            f = link_manager(msg['text'])
            if f != -1:
                await self.sender.sendMessage('File uploading...')
                await self.sender.sendDocument(f)
                if f.name[f.name.rfind('.'):] == '.torrent':  # If the file is a torrent file
                    copyfile(f.name, torrent_path + f.name)  # Copy to torrent directory
                clean_file(f)
                print('Link processed.')
                return
            else:
                print("URL processing failed.")
                await self.sender.sendMessage("URL processing failed.\n"
                                              "Note that some security services block file scraping.\n"
                                              "To solve this send .torrent file directly.\n\n"
                                              + functionality_rundown)
                return

        elif content_type == 'document':  # If message contains a file ---------------------------------------
            file_name = msg['document']['file_name']
            print('File received...')
            if file_name[file_name.rfind('.'):] != '.torrent':
                await self.sender.sendMessage('Only .torrent files are supported.\n\n' + functionality_rundown)
                print('Improper file type, aborted.')
                return
            file_info = await bot.getFile(msg['document']['file_id'])
            # getFile returns a download link to a file hosted by telegram, scrape it with the link_manager function
            f = link_manager("https://api.telegram.org/file/bot" + TOKEN + "/" + file_info['file_path'])
            with open(torrent_path + msg['document']['file_name'], 'wb') as wb:
                wb.write(f.read())
            clean_file(f)
            await self.sender.sendMessage('File moved to torrent directory.')
            print('Torrent file successfully processed.')
            return

        elif content_type == 'photo':  # If message contains an image ----------------------------------------
            await self.sender.sendMessage('Images are not supported. \n\n' + functionality_rundown)
            return


bot = telepot.aio.DelegatorBot(TOKEN, [
    pave_event_space()(
        per_chat_id(), create_open, MessageHandler, timeout=86400),  # Time out after 24hrs
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())
print('Bot started...')

loop.run_forever()
