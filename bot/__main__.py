from aiogram import executor

from clip_bot import dp as dispatcher

executor.start_polling(dispatcher, skip_updates=True)
