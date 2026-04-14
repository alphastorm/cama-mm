import pytest

from utils.interaction_safety import fetch_message, safe_followup


class _StubFollowup:
    def __init__(self):
        self.last_kwargs = None

    async def send(self, **kwargs):
        self.last_kwargs = kwargs
        return "ok"


class _StubResponse:
    def is_done(self):
        return False


class _StubInteraction:
    def __init__(self):
        self.id = 123
        self.followup = _StubFollowup()
        self.response = _StubResponse()
        self.channel = None


class _StubChannel:
    def __init__(self):
        self.fetched_message_id = None

    async def fetch_message(self, message_id):
        self.fetched_message_id = message_id
        return {"message_id": message_id}


class _StubBot:
    def __init__(self, cached_channel=None, fetched_channel=None):
        self.cached_channel = cached_channel
        self.fetched_channel = fetched_channel
        self.get_channel_calls = []
        self.fetch_channel_calls = []

    def get_channel(self, channel_id):
        self.get_channel_calls.append(channel_id)
        return self.cached_channel

    async def fetch_channel(self, channel_id):
        self.fetch_channel_calls.append(channel_id)
        return self.fetched_channel


@pytest.mark.asyncio
async def test_safe_followup_does_not_raise_due_to_dbg():
    interaction = _StubInteraction()

    result = await safe_followup(interaction, content="hi", ephemeral=True)

    assert result == "ok"
    assert interaction.followup.last_kwargs["content"] == "hi"
    assert interaction.followup.last_kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_fetch_message_uses_cached_channel():
    channel = _StubChannel()
    bot = _StubBot(cached_channel=channel)

    message = await fetch_message(bot, 111, 222)

    assert message == {"message_id": 222}
    assert bot.get_channel_calls == [111]
    assert bot.fetch_channel_calls == []
    assert channel.fetched_message_id == 222


@pytest.mark.asyncio
async def test_fetch_message_fetches_channel_when_missing_from_cache():
    channel = _StubChannel()
    bot = _StubBot(cached_channel=None, fetched_channel=channel)

    message = await fetch_message(bot, 333, 444)

    assert message == {"message_id": 444}
    assert bot.get_channel_calls == [333]
    assert bot.fetch_channel_calls == [333]
    assert channel.fetched_message_id == 444


@pytest.mark.asyncio
async def test_fetch_message_returns_none_for_missing_ids():
    bot = _StubBot()

    assert await fetch_message(bot, None, 444) is None
    assert await fetch_message(bot, 333, None) is None
    assert bot.get_channel_calls == []
    assert bot.fetch_channel_calls == []
