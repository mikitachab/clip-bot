import logging

from aiogram import executor

from clip_bot import dp as dispatcher


async def on_shutdown(dp):
    logging.info("closing storage connection")
    await dp.storage.close()
    await dp.storage.wait_closed()


def main():
    executor.start_polling(
        dispatcher,
        skip_updates=True,
        on_shutdown=on_shutdown,
    )


if __name__ == "__main__":
    main()
