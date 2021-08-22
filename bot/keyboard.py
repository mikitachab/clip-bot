from aiogram import types

from callback_data import timecode_cb, confirm_cb, start_clip_cb
import timecode as tc


def confirm_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("create", callback_data=confirm_cb.new(confirm_choice="create")))
    keyboard.add(types.InlineKeyboardButton("cancel", callback_data=confirm_cb.new(confirm_choice="cancel")))
    return keyboard


def timecode_keyboard(timecode: str):
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


def start_clip_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("create", callback_data=start_clip_cb.new(start_clip_choice="create")))
    keyboard.add(types.InlineKeyboardButton("no", callback_data=start_clip_cb.new(start_clip_choice="cancel")))
    return keyboard
