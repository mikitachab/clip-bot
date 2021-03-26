import argparse
import os
import logging


from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
import dotenv

import yt
import fsutils

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()
storage = MemoryStorage()
dp = Dispatcher(Bot(token=os.getenv("BOT_TOKEN")), storage=storage)

class Form(StatesGroup):
    url = State()
    duration = State()


@dp.message_handler(commands=["start", "help", "restart"])
async def start(event: types.Message):
    await event.answer(
        f"Hello, {event.from_user.get_mention(as_html=True)} 👋!",
        parse_mode=types.ParseMode.HTML,
    )

@dp.message_handler(state="*", commands="cancel")
@dp.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=["clip"])
async def clip(message: types.Message):
    await Form.url.set()
    await message.reply("Hi, please send video url")


@dp.message_handler(state=Form.url)
async def process_url(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["url"] = message.text

    await Form.next()
    await message.reply("How long clip should be in seconds?")


@dp.message_handler(state=Form.duration)
async def process_duration(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        logging.info("handle invalid duration")
        await message.reply("Duration gotta be a number.\nHow long clip should be in seconds? (digits only)")
    else:
        async with state.proxy() as data:
            data["duration"] = int(message.text)
        # await message.reply(f"{data["url"]} {data["duration"]}")
        url = data["url"]
        duration = data["duration"]

        with fsutils.mkstemp(".mp4") as output_file:
            video = yt.YouTubeVideo(url)
            video.make_clip(duration, output_file)
            await message.answer_video(open(output_file, "rb"))

        await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
