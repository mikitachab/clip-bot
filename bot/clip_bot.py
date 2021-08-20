import argparse
import os
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BadRequest

import dotenv

import youtube as yt
import timecode as tc
from start_option import StartOption
from clip_info import ClipInfo
from callback_data import timecode_cb, confirm_cb
from keyboard import confirm_keyboard, timecode_keyboard
from text import text as t

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)

if not os.getenv("TEST"):
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage", choices=["redis", "memory"], default="memory")
    args = parser.parse_args()
    storage_type = args.storage
else:
    storage_type = "memory"


def make_storage():
    if storage_type == "redis":
        return RedisStorage(
            host=os.getenv("REDIS_URL"),
            port=int(os.getenv("REDIS_PORT")),
        )
    return MemoryStorage()


bot = Bot(token=os.getenv("BOT_TOKEN"), validate_token=False)
dp = Dispatcher(bot, storage=make_storage())


class Form(StatesGroup):
    url = State()
    start = State()
    duration = State()
    confirm = State()


@dp.message_handler(commands=["start", "help", "restart"])
async def start_handler(message: types.Message):
    await message.answer(
        f"Hello, {message.from_user.get_mention(as_html=True)} 👋!",
        parse_mode=types.ParseMode.HTML,
    )


@dp.message_handler(commands=["clip"])
async def clip_handler(message: types.Message):
    await Form.url.set()
    await message.reply(t.url.question)


@dp.message_handler(state="*", commands=["cancel"])
@dp.message_handler(Text(equals="cancel", ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await message.reply(t.cancelled, reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.url)
async def process_url_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        url = message.text
        data["url"] = url
        yt_url = yt.YTUrl(url)

    await Form.next()
    await message.reply(t.start.question, reply_markup=timecode_keyboard(yt_url.timecode))


@dp.message_handler(state=Form.duration)
async def process_duration_handler(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply(t.duration.invalid)
    else:
        async with state.proxy() as data:
            data["duration"] = int(message.text)

        await Form.next()
        await send_confirm(message.chat.id, state)


@dp.callback_query_handler(timecode_cb.filter(start_choice="provide_timecode"), state=Form.start)
async def provide_timecode_handler(query: types.CallbackQuery):
    await bot.edit_message_text(t.start.choice.provide_timecode, query.from_user.id, query.message.message_id)
    await bot.send_message(query.message.chat.id, t.start.timecode.question)


@dp.callback_query_handler(timecode_cb.filter(start_choice="use_timecode"), state=Form.start)
async def use_timecode_handler(query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(t.start.choice.url_timecode, query.from_user.id, query.message.message_id)
    async with state.proxy() as data:
        data["start"] = StartOption.timecode(yt.YTUrl(data["url"]).timecode)
    await Form.next()
    await query.message.reply(t.duration.question)


@dp.callback_query_handler(timecode_cb.filter(start_choice="from_start"), state=Form.start)
async def from_start_handler(query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(t.start.choice.from_start, query.from_user.id, query.message.message_id)
    async with state.proxy() as data:
        data["start"] = StartOption.from_start()
    await Form.next()
    await query.message.reply(t.duration.question)


@dp.message_handler(state=Form.start)
async def process_timecode_handler(message: types.Message, state: FSMContext):
    try:
        timecode = tc.make_timecode(message.text)
    except tc.InvalidTimecodeError:
        await message.reply(t.start.timecode.invalid)
    else:
        async with state.proxy() as data:
            data["start"] = StartOption.timecode(timecode)
        await Form.next()
        await message.reply(t.duration.question)


@dp.callback_query_handler(confirm_cb.filter(confirm_choice="create"), state=Form.confirm)
async def confirm_handler(query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text(t.clip.creating, query.from_user.id, query.message.message_id)
    try:
        await make_and_send_clip(state, query.message.chat.id)
    except BadRequest as exc:
        logging.exception(exc)
        await bot.send_message(query.message.chat.id, t.error)
    finally:
        await state.finish()


@dp.callback_query_handler(confirm_cb.filter(confirm_choice="cancel"), state=Form.confirm)
async def confirm_cancel_handle(query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await bot.edit_message_text(t.cancelled, query.from_user.id, query.message.message_id)


async def send_confirm(chat_id: int, state: FSMContext):
    async with state.proxy() as data:
        text = make_clip_confirm_text(data)
    await bot.send_message(chat_id, text, reply_markup=confirm_keyboard())


def make_clip_confirm_text(clip_data: dict) -> str:
    return t.confirm.format(
        url=clip_data["url"], duration=clip_data["duration"], start=StartOption(clip_data["start"]).text()
    )


async def make_and_send_clip(state: FSMContext, chat_id: int):
    async with state.proxy() as data:
        logging.info("creating clip: %s", data)
        clip_info = ClipInfo.from_data(data)
        with yt.YTVideo(clip_info.url).make_clip_temp(clip_info.duration, start=clip_info.start) as video_file:
            with open(video_file, "rb") as file:
                await bot.send_video(chat_id, file)
