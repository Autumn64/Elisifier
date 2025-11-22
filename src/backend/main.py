""" Elisifier; A free online music downloader
Copyright (C) 2025  Mónica Gómez (Autumn64)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
# Para poder enviar mensajes por el socket de manera asíncrona. Debe ir arriba de todo,
# ya que de lo contrario tira error.
import eventlet
eventlet.monkey_patch()

import os
import json
from flask import Flask, send_from_directory, request
from downloader import Downloader
from flask_socketio import SocketIO, emit, join_room, leave_room

# Constantes referentes a las rutas absolutas que se utilizarán.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "download")
SCRIPTS_PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SCRIPTS_PATH, "settings.json"), "r") as f:
    config: dict = json.load(f)

app = Flask(__name__)
socket = SocketIO(app, cors_allowed_origins=config["cors"])

@socket.on("download")
def startDownload(args):
# Cuando el socket reciba la señal `download` y si la URL es admitida, comenzará el proceso de descarga.

    # Usa la sesión actual para intercambiar mensajes sólo con ese cliente en específico
    # (sin esto todos los clientes reciben los mismos mensajes y se vuelve un desastre).
    room = request.sid
    join_room(room)

    urls = args['data']["urls"].split(" ")
    accepted = config["accepted"]

    is_valid = all(
        any(acc in url for acc in accepted)
        for url in urls
    )

    if config["block_foreign_urls"] and not is_valid:
        emit("fatal_error", {
            "message": "Sólo puedes introducir URLs de YouTube e Invidious. Puede que algunas instancias de Invidious no sean aceptadas si tienen una URL extraña."
        })
        return

    downloader = Downloader(
        socket = socket,
        room = room,
        folder = DOWNLOAD_FOLDER,
        urls = urls,
        fmt = args['data']["fmt"],
        script = os.path.join(SCRIPTS_PATH, "download.sh"),
        rmscript = os.path.join(SCRIPTS_PATH, "rmcache.sh")
    )

    downloader.runDownload()

    del downloader

@app.route("/downloads/<path:filename>", methods=["GET"])
def downloadFile(filename):
# No expone los archivos directamente en el servidor, sino que lo hace de forma segura mediante un recurso.
    return send_from_directory(DOWNLOAD_FOLDER, filename, download_name="elisifier_dl.zip", as_attachment=True)

if __name__ == "__main__":  
    socket.run(app, host=config["host"], port=config["port"])