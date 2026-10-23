"""ChunkChannel: ordering, backpressure and close semantics."""

import asyncio

import pytest
from papyrium.core.channel import ChannelClosedError, ChunkChannel


async def test_chunks_arrive_in_order():
    channel = ChunkChannel()
    await channel.send(b"A")
    await channel.send(b"B")
    channel.close()
    assert [chunk async for chunk in channel] == [b"A", b"B"]


async def test_empty_chunks_are_dropped():
    channel = ChunkChannel()
    await channel.send(b"")
    channel.close()
    assert [chunk async for chunk in channel] == []


async def test_send_waits_while_the_channel_is_full():
    channel = ChunkChannel(capacity=1)
    await channel.send(b"A")
    blocked = asyncio.create_task(channel.send(b"B"))
    await asyncio.sleep(0.01)
    assert not blocked.done()
    assert await anext(channel) == b"A"
    await asyncio.wait_for(blocked, 1.0)
    assert await anext(channel) == b"B"


async def test_close_delivers_chunks_already_queued():
    channel = ChunkChannel(capacity=2)
    await channel.send(b"A")
    await channel.send(b"B")
    channel.close()
    assert [chunk async for chunk in channel] == [b"A", b"B"]


async def test_close_wakes_a_waiting_reader():
    channel = ChunkChannel()
    reader = asyncio.create_task(anext(channel))
    await asyncio.sleep(0.01)
    channel.close()
    with pytest.raises(StopAsyncIteration):
        await asyncio.wait_for(reader, 1.0)


async def test_send_after_close_is_an_error():
    channel = ChunkChannel()
    channel.close()
    with pytest.raises(ChannelClosedError):
        await channel.send(b"A")


async def test_a_cancelled_read_loses_nothing():
    channel = ChunkChannel()
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(anext(channel), 0.01)
    await channel.send(b"A")
    assert await anext(channel) == b"A"
