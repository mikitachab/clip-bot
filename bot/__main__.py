import logging

from aiogram import executor

from clip_bot import dp as dispatcher


async def on_shutdown(dispatcher):
    logging.info("closing storage connection")
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


def main():
    executor.start_polling(
        dispatcher,
        skip_updates=True,
        on_shutdown=on_shutdown,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
