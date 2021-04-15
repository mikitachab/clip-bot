from unittest.mock import AsyncMock, MagicMock

import pytest

import clip_bot


@pytest.fixture
def form_mock(monkeypatch):
    _form_mock = AsyncMock()
    monkeypatch.setattr(clip_bot, "Form", _form_mock)
    return _form_mock


@pytest.mark.asyncio
async def test_clip_handler(monkeypatch, form_mock):
    message_mock = AsyncMock()

    await clip_bot.clip_handler(message=message_mock)

    form_mock.url.set.assert_called()
    message_mock.reply.assert_called()


@pytest.mark.asyncio
async def test_cancel_handler_no_state():
    message_mock = AsyncMock()
    state_mock = AsyncMock()
    state_mock.get_state.return_value = None

    await clip_bot.cancel_handler(message=message_mock, state=state_mock)

    state_mock.finish.assert_not_called()
    message_mock.reply.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_handler():
    message_mock = AsyncMock()
    state_mock = AsyncMock()
    state_mock.get_state.return_value = "State"

    await clip_bot.cancel_handler(message=message_mock, state=state_mock)

    state_mock.finish.assert_called()
    message_mock.reply.assert_called()


class ProxyMock:
    def __init__(self):
        self.data = {}

    async def __aenter__(self):
        return self.data

    async def __aexit__(self, *args):
        pass


@pytest.mark.asyncio
async def test_process_url_handler(form_mock):
    text = "test message"
    message_mock = AsyncMock()
    message_mock.text = text
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.process_url_handler(message=message_mock, state=state_mock)

    form_mock.next.assert_called()
    message_mock.reply.assert_called()
    assert proxy_mock.data["url"] == text


@pytest.mark.asyncio
async def test_process_duration_handler(form_mock):
    text = "42"
    message_mock = AsyncMock()
    message_mock.text = text
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    proxy_mock.data["url"] = "dummy_url"
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.process_duration_handler(message=message_mock, state=state_mock)

    form_mock.next.assert_called()
    message_mock.reply.assert_called()
    assert "reply_markup" in message_mock.reply.call_args.kwargs.keys()
    assert proxy_mock.data["duration"] == 42


@pytest.mark.asyncio
async def test_process_duration_handler_invalid_input(form_mock):
    text = "text"
    message_mock = AsyncMock()
    message_mock.text = text
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.process_duration_handler(message=message_mock, state=state_mock)

    form_mock.next.assert_not_called()
    message_mock.reply.assert_called()
    assert "duration" not in proxy_mock.data.keys()
