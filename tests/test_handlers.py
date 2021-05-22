from unittest.mock import AsyncMock, MagicMock

import pytest

import clip_bot


@pytest.fixture
def form_mock(monkeypatch):
    _form_mock = AsyncMock()
    monkeypatch.setattr(clip_bot, "Form", _form_mock)
    return _form_mock


@pytest.fixture
def bot_mock(monkeypatch):
    _bot_mock = AsyncMock()
    monkeypatch.setattr(clip_bot, "bot", _bot_mock)
    return _bot_mock


@pytest.fixture
def send_confirm_mock(monkeypatch):
    _mock = AsyncMock()
    monkeypatch.setattr(clip_bot, "send_confirm", _mock)
    return _mock


@pytest.mark.asyncio
async def test_start_handler():
    message_mock = AsyncMock()
    message_mock.from_user = MagicMock()
    await clip_bot.start_handler(message=message_mock)
    message_mock.answer.assert_called()


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

    async def __aexit__(self, *_args):
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
async def test_process_duration_handler(form_mock, bot_mock):
    text = "42"
    message_mock = AsyncMock()
    message_mock.text = text
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    proxy_mock.data["url"] = "dummy_url"
    proxy_mock.data["start"] = "from_start;"
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.process_duration_handler(message=message_mock, state=state_mock)

    form_mock.next.assert_called()
    bot_mock.send_message.assert_called()
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


@pytest.mark.asyncio
async def test_provide_timecode(bot_mock, form_mock):
    query_mock = AsyncMock()

    await clip_bot.provide_timecode_handler(query=query_mock)

    bot_mock.edit_message_text.assert_called()
    bot_mock.send_message.assert_called()
    form_mock.next.assert_called()


@pytest.fixture
def make_and_send_clip_mock(monkeypatch):
    _make_and_send_clip_mock = AsyncMock()
    monkeypatch.setattr(clip_bot, "make_and_send_clip", _make_and_send_clip_mock)
    return _make_and_send_clip_mock


@pytest.mark.asyncio
async def test_use_timecode_handler(bot_mock, form_mock, send_confirm_mock):
    query_mock = AsyncMock()
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    proxy_mock.data["url"] = "test"
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.use_timecode_handler(query=query_mock, state=state_mock)

    bot_mock.edit_message_text.assert_called()
    form_mock.next.assert_called()


@pytest.mark.asyncio
async def test_from_start_handler(bot_mock, form_mock, send_confirm_mock):
    query_mock = AsyncMock()
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.from_start_handler(query=query_mock, state=state_mock)

    bot_mock.edit_message_text.assert_called()
    form_mock.next.assert_called()


@pytest.mark.asyncio
async def test_process_timecode_handler(form_mock, send_confirm_mock):
    message_mock = AsyncMock()
    message_mock.text = "3m2s"
    state_mock = MagicMock()
    proxy_mock = ProxyMock()
    state_mock.proxy.return_value = proxy_mock

    await clip_bot.process_timecode_handler(message=message_mock, state=state_mock)

    form_mock.next.assert_called()
    send_confirm_mock.assert_called()


@pytest.mark.asyncio
async def test_process_timecode_handler_invalid_timecode(make_and_send_clip_mock):
    message_mock = AsyncMock()
    message_mock.text = "some text"
    state_mock = AsyncMock()

    await clip_bot.process_timecode_handler(message=message_mock, state=state_mock)

    state_mock.finish.assert_not_called()
    make_and_send_clip_mock.assert_not_called()
    message_mock.reply.assert_called()


@pytest.mark.asyncio
async def test_confirm_handler(make_and_send_clip_mock, bot_mock):
    query_mock = MagicMock()
    state_mock = AsyncMock()

    await clip_bot.confirm_handler(query=query_mock, state=state_mock)

    state_mock.finish.assert_called()
    make_and_send_clip_mock.assert_called()
