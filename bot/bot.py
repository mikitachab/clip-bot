import os
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData

import dotenv

import youtube as yt
import timecode as tc

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()
storage = MemoryStorage()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot, storage=storage)
timecode_cb = CallbackData("start", "start_choice")


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


@dp.message_handler(commands=["clip"])
async def clip_handler(message: types.Message):
    await Form.url.set()
    await message.reply("Hi, please send video url")


@dp.message_handler(state="*", commands="cancel")
@dp.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.url)
async def process_url_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["url"] = message.text

    await Form.next()
    await message.reply("How long clip should be")


@dp.message_handler(state=Form.duration)
async def process_duration_handler(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Duration gotta be a number.\nHow long clip should be in seconds? (digits only)")
    else:
        async with state.proxy() as data:
            data["duration"] = int(message.text)
            yt_url = yt.YTUrl(data["url"])

        await Form.next()
        await message.reply("Start question?", reply_markup=get_keyboard(yt_url.timecode))


@dp.callback_query_handler(timecode_cb.filter(start_choice="provide_timecode"), state=Form.start)
async def provide_timecode(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await bot.edit_message_text("you choosed to provide timecode", query.from_user.id, query.message.message_id)
    await bot.send_message(query.message.chat.id, "Please provide timecode in seconds")


@dp.callback_query_handler(timecode_cb.filter(start_choice="use_timecode"), state=Form.start)
async def use_timecode(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await bot.edit_message_text("you choosed use timecode", query.from_user.id, query.message.message_id)
    await make_and_send_clip(state, query.message.chat.id)
    await state.finish()


@dp.callback_query_handler(timecode_cb.filter(start_choice="from_start"), state=Form.start)
async def from_start(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await bot.edit_message_text("you choosed from start", query.from_user.id, query.message.message_id)
    try:
        await make_and_send_clip(state, query.message.chat.id, start=0)
        await state.finish()
    except tc.InvalidTimecodeError:
        await message.reply("Timecode should has valid format\nPlease provide timecode")


@dp.message_handler(state=Form.start)
async def process_timecode(message: types.Message, state: FSMContext):
    try:
        timecode = tc.make_timecode(message.text)
    except tc.InvalidTimecodeError:
        await message.reply("Timecode should has valid format\nPlease provide timecode")
    else:
        await make_and_send_clip(state, message.chat.id, start=timecode.seconds)
        await state.finish()


async def make_and_send_clip(state: FSMContext, chat_id: int, start: Optional[int] = None):
    async with state.proxy() as data:
        yt_url = yt.YTUrl(data["url"])
        if start is None:
            start = tc.make_timecode(yt_url.timecode).seconds
        with yt.YTVideo(yt_url).make_clip_temp(data["duration"], start=start) as video_file:
            await bot.send_video(chat_id, open(video_file, "rb"))


def get_keyboard(timecode):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("from start", callback_data=timecode_cb.new(start_choice="from_start")))
    keyboard.add(
        types.InlineKeyboardButton(
            "provide timecode",
            callback_data=timecode_cb.new(start_choice="provide_timecode"),
        )
    )
    if timecode and tc.is_valid_timecode(timecode):
        keyboard.add(
            types.InlineKeyboardButton(
                f"use timecode ({timecode})",
                callback_data=timecode_cb.new(start_choice="use_timecode"),
            )
        )
    return keyboard
