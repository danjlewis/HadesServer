import threading
import websockets
import asyncio
import json
import enum
import dataclasses
import uuid

@enum.unique
class IncomingMessageType(enum.Enum):
    REPL = enum.auto()
    DATA = enum.auto()

@dataclasses.dataclass
class IncomingMessage:
    type: IncomingMessageType
    data: any = None
    request_uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

def parse_incoming_message(msg):
    obj = None
    try:
        obj = json.loads(msg)
    except json.JSONDecodeError:
        return (None, None)

    if "request_uuid" not in obj:
        obj["request_uuid"] = str(uuid.uuid4())
    if type(obj["request_uuid"]) != str:
        return (None, None)

    if "type" not in obj:
        return (None, obj["request_uuid"])
    if type(obj["type"]) != str:
        return (None, obj["request_uuid"])

    if "data" not in obj:
        obj["data"] = (None, obj["request_uuid"])

    INCOMING_MESSAGE_TYPE_CODES = {"repl": IncomingMessageType.REPL, "data": IncomingMessageType.DATA}
    if obj["type"] not in INCOMING_MESSAGE_TYPE_CODES:
        return (None, obj["request_uuid"])
    msg_type = INCOMING_MESSAGE_TYPE_CODES[obj["type"]]

    return (IncomingMessage(msg_type, obj["data"], obj["request_uuid"]), obj["request_uuid"])

def run():
    async def handler(socket):
        print("Client connected!")

        async def hook(msg):
            if not socket.open:
                return

            await socket.send(msg)
        Scribe.AddHook(hook, "Out: ")

        async for raw_msg in socket:
            msg, uuid = parse_incoming_message(raw_msg)

            uuid_msg = "unknown request UUID" if uuid is None else f"request {msg.request_uuid}"
            if msg is None:
                await socket.send(f"Invalid message format! ({uuid_msg})")
                continue

            if msg.type == IncomingMessageType.REPL:
                if type(msg.data) != str:
                    await socket.send(f"Invalid message format! ({uuid_msg})")
                    continue

                Scribe.Modules.StyxScribeREPL.RunLua(msg.data)

        print("Client disconnected.")

    async def run():
        PORT = 8000
        async with websockets.serve(handler, "0.0.0.0", PORT):
            print(f"Listening on port {PORT}...")

            await asyncio.Future()
    asyncio.run(run())

def Load():
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
