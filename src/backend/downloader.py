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

import os
import re
import uuid
import shutil
import subprocess

# Utilizo un script en lugar de la librería nativa de `yt-dlp` porque, de hecho, traté de hacer
# eso la primera vez, y fue un martirio. Prefiero no sufrir y usarlo como un programa de línea
# de comandos, que es algo que domino mucho más.

# El socket puede transmitir 6 tipos de mensaje desde aquí: `output`, `progress`, `status`, `success`,
# `error` y `fatal_error`. Respectivamente, corresponden a:
#     - Los mensajes que se muestran en el `outputDiv` del frontend.
#     - La barra de progreso con el porcentaje de la descarga.
#     - El mensaje que se muestra en `infoMsg`.
#     - El mensaje que se muestra en `successMsg`.
#     - El mensaje que se muestra en `errorMsg`.
#     - También un mensaje de error, pero cancela la acción en curso y regresa
#       a la pantalla principal.

# Estos mensajes se pueden aplicar en otros frontends, realizando las adaptaciones adecuadas.

class Downloader():
    def __init__(self, socket, room, folder, urls, fmt, script, rmscript):
        self.socket = socket
        self.room = room
        self.urls = urls
        self.fmt = fmt
        self.script = script # Ruta del script a ejecutar
        self.rmscript = rmscript # Ruta del script que limpiará los archivos
        self.uuid = str(uuid.uuid4()) # ID único para la descarga actual
        self.errors = False # Comprobación de errores
        self.path = os.path.join(folder, self.uuid)

    def runDownload(self):
    # Ejecuta el script `download.sh` y captura STDOUT para enviarlo por el socket
        # Desempaqueta la lista de las urls
        ydl = subprocess.Popen(stdout=subprocess.PIPE, text=True, args=[self.script, self.path, self.fmt, *self.urls])
        playlist = ""

        while (line := ydl.stdout.readline()) != "":
            dLine = line.rstrip()
            self.socket.emit("output", {"message": dLine}, room=self.room)

            # Comprobación si no se pudo descargar ningún archivo
            if "FATAL ERROR:" in dLine:
                self.socket.emit("fatal_error", {"message": "No se pudo descargar la música. Inténtalo de nuevo más tarde."}, room=self.room)
                self.removeAll(False)
                return

            # Si una o más canciones no se pudieron descargar, notifica y continúa
            if "ERROR:" in dLine and self.errors == False:
                self.errors = True
            
            # Si se está descargando una playlist, extrae su nombre
            if "Downloading playlist:" in dLine:
                playlist = f" de la playlist `{dLine.split(':')[-1].strip()}`"

            # Extrae la canción actualmente en descarga y el total de canciones de la playlist para calcular el progreso
            if "Downloading item" in dLine and playlist != "":
                regex = re.search(r'item (\d+) of (\d+)', dLine)
                if not regex: continue
                
                n1 = regex.group(1); n2 = regex.group(2)
                self.socket.emit("status", {
                    "message": f"Descargando canción {n1} de {n2}{playlist}"
                }, room=self.room)
            
            # Resetea la barra de progreso a cero
            if "Sleeping" in dLine:
                self.socket.emit("progress", {
                    "percentage": 0,
                }, room=self.room)
            
            # Llena la barra de progreso conforme va aumentando el porcentaje de la descarga
            if "[download]" in dLine:
                regex = re.search(r'(\d+)\.(\d+)%', dLine)
                if not regex: continue

                self.socket.emit("progress", {
                    "percentage": regex.group(1),
                }, room=self.room)

            if "Adding cover" in dLine:
                self.socket.emit("progress", {
                    "percentage": 0
                }, room=self.room)

                self.socket.emit("status", {
                    "message": "Procesando, por favor espere..."
                }, room=self.room)

            if "Done." in dLine:
                self.socket.emit("progress", {
                    "percentage": 100
                }, room=self.room)

                self.socket.emit("status", {
                    "message": "Finalizando, por favor espere."
                }, room=self.room)

                self.socket.sleep(2)

                self.makeZip()
                self.removeAll(True)

    def makeZip(self):
    # Guarda la carpeta de descarga en un zip
        shutil.make_archive(self.path, "zip", self.path)
        self.socket.emit("success", {
            "message": "Archivo listo para descargar.",
            "link": f"downloads/{self.uuid}.zip"
        }, room=self.room)

        if self.errors == True:
           self.socket.emit("error", {"message": "Algunas canciones no se descargaron. Quizás tienen restricción de edad o no están disponibles."}, room=self.room)

    def removeAll(self, run_script: bool):
    # Elimina la carpeta de antemano y ejecuta en modo detached el script que eliminará el zip después de un tiempo
        shutil.rmtree(self.path)
        if run_script == False: return
        subprocess.Popen(
            preexec_fn = os.setsid,
            args = [self.rmscript, f"{self.path}.zip"]
        )