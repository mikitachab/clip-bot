from aiogram import executor

from bot import dp as dispatcher

executor.start_polling(dispatcher, skip_updates=True)
