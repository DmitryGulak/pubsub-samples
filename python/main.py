import websocket
import json
import atexit
import ssl
import uuid
from logger import logger

TWITCH_PUB_SUB_URL = 'wss://pubsub-edge.twitch.tv'

ACCESS_TOKEN = 'avpkyafdx422pk7ntjal0ekaxf6e1j'
CHANNEL_ID = '419843389'

TOPICS = [f'channel-points-channel-v1.{CHANNEL_ID}']


def on_reward_redeem(ws, data):
    logger.info(f'Reward redeem: {data}')


def on_reconnect(ws, message):
    logger.info('Got reconnect message, exiting...')
    exit()


TYPE_TO_ACTION = {
    'RECONNECT': on_reconnect,
    'reward-redeemed': on_reward_redeem
}


def on_message(ws, message):
    logger.info(f'Got pub sub message: {message}')
    if isinstance(message, str):
        message = json.loads(message)
    if not message:
        return
    if 'data' not in message:
        return
    message = message.get('data', {}).get('message', {})
    message = json.loads(message)
    logger.info(f'Parsed message is: {message}')
    message_type = message.get('type')
    logger.info(f'Message type is: {message_type}')
    action = TYPE_TO_ACTION.get(message_type)
    logger.info(f'ACTION IS: {action}')
    if action:
        data = message.get('data', {})
        action(ws, data)


def on_error(ws, error):
    logger.error(f'Got error in pub sub: {error}')
    ws.close()
    exit()


def on_close(ws):
    logger.error('Pub sub connection closed')
    ws.close()
    exit()


def close_before_exit(ws):
    logger.info('Got exit message. Closing ws connection')
    ws.close()
    exit()


def register_to_threads(ws):
    payload = {
        'type': 'LISTEN',
        'nonce': str(uuid.uuid4()),
        'data': {
            'topics': TOPICS,
            'auth_token': ACCESS_TOKEN,
        }
    }
    string_payload = json.dumps(payload)
    logger.info(f'Sending message: {string_payload}')
    ws.send(string_payload)


def main():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(TWITCH_PUB_SUB_URL,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = register_to_threads
    atexit.register(close_before_exit, ws=ws)
    ws.run_forever(
        sslopt={"cert_reqs": ssl.CERT_NONE},
        ping_interval=20,
        ping_timeout=10,
    )


if __name__ == '__main__':
    main()
