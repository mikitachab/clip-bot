import os
import logging

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
bot = Bot(token=os.getenv("BOT_TOKEN"), validate_token=False)
dp = Dispatcher(bot, storage=storage)
timecode_cb = CallbackData("start", "start_choice")
confirm_cb = CallbackData("confirm", "confirm_choice")


class Form(StatesGroup):
    url = State()
    duration = State()
    start = State()
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
async def provide_timecode_handler(query: types.CallbackQuery):
    await bot.edit_message_text("you choosed to provide timecode", query.from_user.id, query.message.message_id)
    await bot.send_message(query.message.chat.id, "Please provide timecode in seconds")


class StartOption:
    def __init__(self, option):
        self._option = option

    def text(self):
        if self._option == StartOption.from_start():
            return "from video start"
        return self._option.split(";")[1] + " seconds"

    @staticmethod
    def from_start() -> str:
        return "from_start;"

    @staticmethod
    def timecode(timecode_str) -> str:
        return f"timecode;{timecode_str}"


@dp.callback_query_handler(timecode_cb.filter(start_choice="use_timecode"), state=Form.start)
async def use_timecode_handler(query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text("you choosed use timecode", query.from_user.id, query.message.message_id)
    async with state.proxy() as data:
        data["start"] = StartOption.timecode(yt.YTUrl(data["url"]).timecode)
    await Form.next()
    await send_confirm(query.message.chat.id, state)


@dp.callback_query_handler(timecode_cb.filter(start_choice="from_start"), state=Form.start)
async def from_start_handler(query: types.CallbackQuery, state: FSMContext):
    await bot.edit_message_text("you choosed from start", query.from_user.id, query.message.message_id)
    async with state.proxy() as data:
        data["start"] = StartOption.from_start()
    await Form.next()
    await send_confirm(query.message.chat.id, state)


@dp.message_handler(state=Form.start)
async def process_timecode_handler(message: types.Message, state: FSMContext):
    try:
        timecode = tc.make_timecode(message.text)
    except tc.InvalidTimecodeError:
        await message.reply("Timecode should has valid format\nPlease provide timecode")
    else:
        async with state.proxy() as data:
            data["start"] = StartOption.timecode(timecode)
        await Form.next()
        await send_confirm(message.chat.id, state)


@dp.callback_query_handler(confirm_cb.filter(confirm_choice="create"), state=Form.confirm)
async def confirm_handler(query: types.CallbackQuery, state: FSMContext):
    await make_and_send_clip(state, query.message.chat.id)
    await state.finish()


@dp.callback_query_handler(confirm_cb.filter(confirm_choice="cancel"), state=Form.confirm)
async def confirm_cancel_handle(query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.finish()
    await query.message.reply("Cancelled.", reply_markup=types.ReplyKeyboardRemove())


async def send_confirm(chat_id: int, state: FSMContext):
    async with state.proxy() as data:
        text = make_clip_confirm_text(data)

    await bot.send_message(chat_id, text, reply_markup=get_confirm_keyboard())


def make_clip_confirm_text(clip_data: dict) -> str:
    text = f"URL: {clip_data['url']}\n"
    text += f"Duration: {clip_data['duration']} seconds\n"
    text += f"Start: {StartOption(clip_data['start']).text()}\n"
    return text


async def make_and_send_clip(state: FSMContext, chat_id: int):
    async with state.proxy() as data:
        yt_url = yt.YTUrl(data["url"])
        if data["start"] == StartOption.from_start():
            start = 0
        else:
            start = tc.make_timecode(yt_url.timecode).seconds
        with yt.YTVideo(yt_url).make_clip_temp(data["duration"], start=start) as video_file:
            await bot.send_video(chat_id, open(video_file, "rb"))


def get_confirm_keyboard():
    confirm_keyboard = types.InlineKeyboardMarkup()
    confirm_keyboard.add(types.InlineKeyboardButton("create", callback_data=confirm_cb.new(confirm_choice="create")))
    confirm_keyboard.add(types.InlineKeyboardButton("cancel", callback_data=confirm_cb.new(confirm_choice="cancel")))
    return confirm_keyboard


def get_keyboard(timecode: str):
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
