import threading
import websockets
import asyncio
import json
import enum
import dataclasses
import uuid
import os

LOGGING_PREFIX = "HadesServer: "

@enum.unique
class IncomingMessageType(enum.Enum):
    REPL = enum.auto()
    READ_DATA = enum.auto()

@dataclasses.dataclass
class IncomingMessage:
    type: IncomingMessageType
    data: any = None
    request_uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

    @staticmethod
    def deserialize(s):
        obj = None
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            return (None, {"error": "invalid JSON", "request_uuid": None})

        if "request_uuid" not in obj:
            obj["request_uuid"] = str(uuid.uuid4())
        if type(obj["request_uuid"]) != str:
            return (None, {"error": "invalid `request_uuid` field type", "request_uuid": None})

        if "type" not in obj:
            return (None, {"error": "missing `type` field", "request_uuid": obj["request_uuid"]})
        if type(obj["type"]) != str:
            return (None, {"error": "invalid `type` field type", "request_uuid": obj["request_uuid"]})

        if "data" not in obj:
            obj["data"] = None

        INCOMING_MESSAGE_TYPE_CODES = {"repl": IncomingMessageType.REPL, "read_data": IncomingMessageType.READ_DATA}
        if obj["type"] not in INCOMING_MESSAGE_TYPE_CODES:
            return (None, {"error": "invalid `type` field value", "request_uuid": obj["request_uuid"]})
        msg_type = INCOMING_MESSAGE_TYPE_CODES[obj["type"]]

        return (IncomingMessage(msg_type, obj["data"], obj["request_uuid"]), None)

@enum.unique
class OutgoingMessageType(enum.Enum):
    REPL_OUTPUT = enum.auto()
    DATA_OUTPUT = enum.auto()
    ERROR = enum.auto()

@dataclasses.dataclass
class OutgoingMessage:
    type: OutgoingMessageType
    data: any = None
    request_uuid: str = None

    def serialize(self):
        obj = dataclasses.asdict(self)
        # obj = {"type": self.type, "data": self.data, "request_uuid": self.request_uuid}

        OUTGOING_MESSAGE_TYPE_CODES = {OutgoingMessageType.REPL_OUTPUT: "repl_output", OutgoingMessageType.DATA_OUTPUT: "data_output", OutgoingMessageType.ERROR: "error"}
        obj["type"] = OUTGOING_MESSAGE_TYPE_CODES[obj["type"]]

        obj = {k: v for k, v in obj.items() if v is not None}

        return json.dumps(obj)

def convert_shared_data(obj):
    if hasattr(obj, "_proxy"):
        obj = getattr(obj, "_proxy")

    if type(obj) in (list, tuple):
        obj = [convert(x) for x in obj]
        for x in obj:
            print(type(x))
    elif type(obj) == set:
        obj = {convert(x): True for x in obj}
        for k, v in obj.items():
            print(type(k), type(v))
    elif type(obj) == dict:
        obj = {k: convert(v) for k, v in obj.items()}
        for k, v in obj.items():
            print(type(k), type(v))

    return obj

async def handler(socket):
    print(LOGGING_PREFIX + "Client connected!")

    async def hook(output):
        if not socket.open:
            return

        request_uuid = None
        if output.startswith("Request "):
            output_split = output.split(": ")
            request_uuid = output_split[0][8:]
            output = "".join(output_split[1:])

        await socket.send(OutgoingMessage(OutgoingMessageType.REPL_OUTPUT, output, request_uuid).serialize())
    Scribe.AddHook(hook, "Response: ")

    async for msg in socket:
        msg, err = IncomingMessage.deserialize(msg)

        if err is not None:
            await socket.send(OutgoingMessage(OutgoingMessageType.ERROR, err["error"], err["request_uuid"]).serialize())
            continue

        match msg.type:
            case IncomingMessageType.REPL:
                if type(msg.data) != str:
                    await socket.send(OutgoingMessage(OutgoingMessageType.ERROR, "invalid `data` field type", msg.request_uuid).serialize())
                    continue

                Scribe.Send(f"StyxScribeREPL: Request {msg.request_uuid}: {msg.data}")
            case IncomingMessageType.READ_DATA:
                if type(msg.data) != str:
                    await socket.send(OutgoingMessage(OutgoingMessageType.ERROR, "invalid `data` field type", msg.request_uuid).serialize())
                    continue
                if msg.data not in Scribe.Modules.StyxScribeShared.Root:
                    await socket.send(OutgoingMessage(OutgoingMessageType.ERROR, "unknown data key", msg.request_uuid).serialize())
                    continue

                data = convert_shared_data(Scribe.Modules.StyxScribeShared.Root[msg.data])
                await socket.send(OutgoingMessage(OutgoingMessageType.DATA_OUTPUT, data, msg.request_uuid).serialize())

    print(LOGGING_PREFIX + "Client disconnected.")

def run():
    async def run():
        port = int(os.environ.get("PORT", "8000"))
        async with websockets.serve(handler, "0.0.0.0", port):
            print(LOGGING_PREFIX + f"Listening on port {port}...")

            await asyncio.Future()
    asyncio.run(run())

def Load():
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
