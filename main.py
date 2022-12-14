import logging
from aiogram import Bot, Dispatcher, executor, types

import os
from ffprobe import FFProbe
from datetime import datetime, timedelta

API_TOKEN = '<BOT-TOKEN>'
UTC_OFFSET = 0
MAX_ALLOWED_DIFF = 60  # seconds

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await bot.send_sticker(msg.from_user.id, "CAACAgIAAxkBAAM9YXfH5sCS-41cwfqE5wF6I25R3U4AAqkRAALI5XFJY-8zAfzb5vghBA")
    await bot.send_message(msg.from_user.id,
                           "<b>✌️Привет!</b>\nПерешли мне видео заметку из чата, чтобы я её проверил.\n\n⚠️<b><i>Внимание!\nДля корректной работы обязательно нужно пересылать заметку из чата с собеседником, это важно.</i></b>\n🕒 Также, пожалуйста, учитывайте что все временные метки указываются в UTC+0.\n\n<i>Видеосообщения не хранятся на сервере и удаляются сразу после проверки.</i>",
                           parse_mode="html")


@dp.message_handler(commands=['help'])
async def help(msg: types.Message):
    await msg.reply("""Крч объясняю про <b>Метаданные</b> в видеосообщениях Телеграм, для тех кто не в курсах.
Когда вам отправляют видеосообщение <i>(круглое такое)</i>, по сути их подделать нельзя - или так кажется, ведь они были записаны только что.

НО, ничто не мешает человеку заранее записать его, закинуть в избранное, и в нужный момент отправить <i>(собеседник подумает, что записано было только что)</i>.
И даже информирование о том, что <i>"Собеседник записывает видеосообщение"</i> можно подделать.
Причем пометку о форварде тоже можно легко убрать <i>(даже на ПК)</i>.

Так вооот 🌚
Оказывается, телеграм прописывает в <b>Метаданные</b> данные файла видеосообщения - точную дату и время записи.
И вот это уже никто почти не знает и фиг подделает.
А значит, чтобы удостовериться что видеосообщение было реально записано тогда, когда его тебе отправили - достаточно сохранить его как файл и взглянуть на свойства файла.

Крч такие дела 🤔
А наш бот позволяет это проверить, просто перешлите сюда видеосообщение из чата с собеседником.""", parse_mode="html")


@dp.message_handler(content_types=types.ContentType.all())
async def check(msg: types.Message):
    if msg.content_type == "video_note":
        #  identify file path
        file = await bot.get_file(msg.video_note.file_id)
        file_path = file.file_path

        # download video note as a file
        if not os.path.exists('temp'):
            os.makedirs('temp')

        local_temp_filename = f"temp/{msg.from_user.id}_{os.path.basename(file_path)}"
        await bot.download_file(file_path, local_temp_filename)

        # retrieve a video note creation_date from a metadata (using FFProbe)
        metadata = FFProbe(local_temp_filename)

        if "creation_time" not in metadata.metadata:
            await msg.reply("В видео заметке отсутствует мета-информация о дате создания записи!")
            return

        _creation_date = datetime.strptime(metadata.metadata["creation_time"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
        creation_date = _creation_date + timedelta(hours=UTC_OFFSET)

        # compare & reply
        if msg.is_forward():
            diff = abs(msg.forward_date - creation_date)
        else:
            diff = abs(msg.date - creation_date)

        answer = f"<b>Дата создания записи: </b><b><i>{creation_date}</i></b>\n"
        answer += f"<b>Дата отправки: </b><b><i>{msg.forward_date if msg.is_forward() else msg.date}</i></b>\n\n"

        if diff.total_seconds() > MAX_ALLOWED_DIFF:
            answer += f"❗️ Разница между датой создания записи и датой отправки слишком большая и превышает <b><i>{MAX_ALLOWED_DIFF}с.</i></b>!!!\n\n<i>Но мы не учитываем длительность видеосообщения и возможные проблемы с сетью у вашего собеседника.</i> "
        else:
            answer += f"✅ Разница между датой создания записи и датой отправки допустимая и составляет всего <b><i>{int(diff.total_seconds())}с.</i></b>"

        await msg.reply(answer, parse_mode="html")

        # remove a file
        os.remove(local_temp_filename)

    else:
        await msg.reply("Принимаются только видео заметки!")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
