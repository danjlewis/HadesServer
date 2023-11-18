import threading
import websockets
import asyncio
import json
import enum
import dataclasses
import uuid

LOGGING_PREFIX = "HadesServer: "

@enum.unique
class IncomingMessageType(enum.Enum):
    REPL = enum.auto()
    DATA = enum.auto()

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

        INCOMING_MESSAGE_TYPE_CODES = {"repl": IncomingMessageType.REPL, "data": IncomingMessageType.DATA}
        if obj["type"] not in INCOMING_MESSAGE_TYPE_CODES:
            return (None, {"error": "invalid `type` field value", "request_uuid": obj["request_uuid"]})
        msg_type = INCOMING_MESSAGE_TYPE_CODES[obj["type"]]

        return (IncomingMessage(msg_type, obj["data"], obj["request_uuid"]), None)

@enum.unique
class OutgoingMessageType(enum.Enum):
    REPL_OUTPUT = enum.auto()
    ERROR = enum.auto()

@dataclasses.dataclass
class OutgoingMessage:
    type: OutgoingMessageType
    data: any = None
    request_uuid: str = None

    def serialize(self):
        obj = dataclasses.asdict(self)

        OUTGOING_MESSAGE_TYPE_CODES = {OutgoingMessageType.REPL_OUTPUT: "repl_output", OutgoingMessageType.ERROR: "error"}
        obj["type"] = OUTGOING_MESSAGE_TYPE_CODES[obj["type"]]

        obj = {k: v for k, v in obj.items() if v is not None}

        return json.dumps(obj)

def run():
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

            if msg.type == IncomingMessageType.REPL:
                if type(msg.data) != str:
                    await socket.send(OutgoingMessage(OutgoingMessageType.ERROR, "invalid `data` field type", msg.request_uuid).serialize())
                    continue

                Scribe.Send(f"StyxScribeREPL: Request {msg.request_uuid}: {msg.data}")

        print(LOGGING_PREFIX + "Client disconnected.")

    async def run():
        PORT = 8000
        async with websockets.serve(handler, "0.0.0.0", PORT):
            print(f"Listening on port {PORT}...")

            await asyncio.Future()
    asyncio.run(run())

def Load():
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
