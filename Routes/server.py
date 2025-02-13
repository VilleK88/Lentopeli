import folium
import webbrowser
import threading
from http.server import SimpleHTTPRequestHandler
import http.server
import asyncio
import websockets
import json
#import socketserver
#from socketserver import TCPServer

PORT = 8000
WS_PORT = 8765
file_path = "../templates/map.html"
url = f"http://127.0.0.1:{PORT}/templates/map.html"
clients = set()

def start_server(latitude, longitude, zoom):
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom)
    m.save(file_path)

    m.get_root().html.add_child(folium.Element("""
            <script>
                var socket = new WebSocket("ws://127.0.0.1:8765/");
                socket.onmessage = function(event) {
                    var data = JSON.parse(event.data);
                    map.setView([data.lat, data.lon], map.getZoom());
                };
            </script>
        """))

    def run_server():
        with http.server.HTTPServer(("127.0.0.1", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            httpd.serve_forever()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    def run_ws_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_websocket_server())

    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()

    webbrowser.open(url)

async def websocket_handler(websocket):
    clients.add(websocket)
    try:
        async for message in websocket:
            for client in clients:
                if client != websocket:
                    await client.send(message)
    finally:
        clients.remove(websocket)

async def start_websocket_server():
    async with websockets.serve(websocket_handler, "127.0.0.1", WS_PORT):
        await asyncio.Future()

def update_server(latitude, longitude, zoom):
    #m = folium.Map(location=[latitude, longitude], zoom_start=zoom)
    #m.save(file_path)
    #webbrowser.open(url, new=0, autoraise=True)
    message = json.dumps({"lat": latitude, "lon": longitude})

    async def send_update():
        async with websockets.connect(f"ws://127.0.0.1:{WS_PORT}/") as websocket:
            await websocket.send(message)

    asyncio.run(send_update())