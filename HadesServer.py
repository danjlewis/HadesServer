import threading
import websockets
import asyncio

PORT = 8000

def run():
    async def handler(socket):
        print("Client connected!")

        async def hook(msg):
            if not socket.open:
                return

            await socket.send(msg)
        Scribe.AddHook(hook, "Out: ")

        async for message in socket:
            Scribe.Modules.StyxScribeREPL.RunLua(message)

        print("Client disconnected.")

    async def run():
        async with websockets.serve(handler, "0.0.0.0", PORT):
            print(f"Listening on port {PORT}...")

            await asyncio.Future()
    asyncio.run(run())

def Load():
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
