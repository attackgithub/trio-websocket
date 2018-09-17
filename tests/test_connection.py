import pytest
from trio_websocket import ConnectionClosed, WebSocketClient, WebSocketServer
import trio


import logging
logging.basicConfig(level=logging.DEBUG)
HOST = 'localhost'
RESOURCE = 'resource'


@pytest.fixture
async def echo_server(nursery):
    ''' An echo server reads one message, sends back the same message,
    then exits. '''
    async def handler(conn):
        try:
            msg = await conn.get_message()
            await conn.send_message(msg)
        except ConnectionClosed:
            pass
    server = WebSocketServer(handler, HOST, 0, ssl_context=None)
    await nursery.start(server.listen)
    yield server


@pytest.fixture
async def echo_conn(echo_server, nursery):
    ''' Return a client connection instance that is connected to an echo
    server. '''
    client = WebSocketClient(HOST, echo_server.port, RESOURCE, use_ssl=False)
    async with await client.connect(nursery) as conn:
        yield conn


async def test_client_send_and_receive(echo_conn, nursery):
    async with echo_conn:
        await echo_conn.send_message('This is a test message.')
        received_msg = await echo_conn.get_message()
        assert received_msg == 'This is a test message.'


async def test_client_default_close(echo_conn, nursery):
    async with echo_conn:
        assert echo_conn.closed is None
    assert echo_conn.closed.code == 1000
    assert echo_conn.closed.reason is None


async def test_client_nondefault_close(echo_conn, nursery):
    async with echo_conn:
        assert echo_conn.closed is None
        await echo_conn.aclose(code=1001, reason='test reason')
    assert echo_conn.closed.code == 1001
    assert echo_conn.closed.reason == 'test reason'