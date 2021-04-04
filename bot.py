import argparse
import contextlib
import dataclasses
import os
import logging
import subprocess
import re
import tempfile
from typing import Optional

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData

import dotenv


logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()
storage = MemoryStorage()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot, storage=storage)
timecode_cb = CallbackData("start", "start_choice")


@contextlib.contextmanager
def mkstemp(suffix=""):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    yield path
    os.remove(path)


class YTUrl:
    def __init__(self, url):
        self._url = url

    def value(self):
        return self._url

    def timecode(self) -> int:
        match = re.search(r".+\?t=(\d+)", self._url)
        if match and hasattr(match, "groups"):
            return match.groups()[0]
        return 0


class YouTubeVideo:
    def __init__(self, url: YTUrl):
        self._url = url

    def make_clip(self, duration: int, out_file: str, start=None):
        start = start if start is not None else self._url.timecode()
        # comes from https://old.reddit.com/r/youtubedl/comments/b67xh5/downloading_part_of_a_youtube_video/ejv5ye7/
        cmd = f"ffmpeg -ss {start} -i $(youtube-dl -f 22 -g {self._url.value()}) -acodec copy -vcodec copy -t {duration} {out_file} -y"
        print(cmd)
        p = subprocess.Popen(cmd, shell=True)
        p.wait()


class Form(StatesGroup):
    url = State()
    duration = State()
    start = State()


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


def get_keyboard(timecode):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("from start", callback_data=timecode_cb.new(start_choice="from_start")))
    keyboard.add(
        types.InlineKeyboardButton(
            "provide timecode",
            callback_data=timecode_cb.new(start_choice="provide_timecode"),
        )
    )
    if timecode:
        keyboard.add(
            types.InlineKeyboardButton(
                f"use timecode ({timecode})",
                callback_data=timecode_cb.new(start_choice="use_timecode"),
            )
        )
    return keyboard


@dp.message_handler(state=Form.duration)
async def process_duration(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        logging.info("handle invalid duration")
        await message.reply("Duration gotta be a number.\nHow long clip should be in seconds? (digits only)")
    else:
        async with state.proxy() as data:
            data["duration"] = int(message.text)
            yt_url = YTUrl(data["url"])

        await Form.next()
        await message.reply(f"Start question?", reply_markup=get_keyboard(yt_url.timecode()))


@dp.callback_query_handler(timecode_cb.filter(start_choice="use_timecode"), state=Form.start)
async def use_timecode(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await bot.edit_message_text("you choosed use_timecode", query.from_user.id, query.message.message_id)
    async with state.proxy() as data:
        url = data["url"]
        duration = data["duration"]
        start = 0
        with mkstemp(".mp4") as video_file:
            yt_url = YTUrl(url)
            video = YouTubeVideo(yt_url)
            video.make_clip(duration, video_file)
            await query.message.answer_video(open(video_file, "rb"))
    await state.finish()


@dp.callback_query_handler(timecode_cb.filter(start_choice="from_start"), state=Form.start)
async def from_start(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await bot.edit_message_text("you choosed from_start", query.from_user.id, query.message.message_id)
    async with state.proxy() as data:
        url = data["url"]
        duration = data["duration"]
        start = 0
        with mkstemp(".mp4") as video_file:
            yt_url = YTUrl(url)
            video = YouTubeVideo(yt_url)
            video.make_clip(duration, video_file, start=0)
            await query.message.answer_video(open(video_file, "rb"))
    await state.finish()


@dp.callback_query_handler(timecode_cb.filter(start_choice="provide_timecode"), state=Form.start)
async def provide_timecode(query: types.CallbackQuery, callback_data: dict):
    async with state.proxy() as data:
        logging.info(data)
    await bot.edit_message_text("you choosed provide_timecode", query.from_user.id, query.message.message_id)
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
