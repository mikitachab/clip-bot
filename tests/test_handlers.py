import pytest
from unittest.mock import AsyncMock

import bot


@pytest.fixture
def form_mock(monkeypatch):
    _form_mock = AsyncMock()
    monkeypatch.setattr(bot, "Form", _form_mock)
    return _form_mock



@pytest.mark.asyncio
async def test_clip_handler(monkeypatch, form_mock):
    message_mock = AsyncMock()

    await bot.clip_handler(message=message_mock)

    form_mock.url.set.assert_called()
    message_mock.reply.assert_called()
