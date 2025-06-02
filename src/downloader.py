# Elisifier; A free online music downloader
# Copyright (C) 2025  Mónica Gómez (Autumn64)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import re
import uuid
import shutil
import subprocess
import streamlit as st

# Utilizo un script en lugar de la librería nativa de `yt-dlp` porque, de hecho, traté de hacer
# eso la primera vez, y fue un martirio. Prefiero no sufrir y usarlo como un programa de línea
# de comandos, que es algo que domino mucho más.

class Downloader():
    def __init__(self, url, fmt, progress, status, script, rmscript):
        self.url = url.split(" ") # Hace split para poder leer todas las urls
        self.fmt = fmt
        self.progress = progress # Debe ser un `st.progress`
        self.status = status # Debe ser un `st.status`
        self.script = script # Ruta del script a ejecutar
        self.rmscript = rmscript # Ruta del script que limpiará los archivos
        self.uuid = str(uuid.uuid4()) # ID único para la descarga actual
    
    # Getter del UUID
    def obtenerUUID(self) -> str:
        return self.uuid

    # Actualiza la barra de progreso de la descarga
    def actualizarProgreso(self, value: float, text: str):
        self.progress.progress(value, text=text)

    # Agrega los mensajes capturados de STDOUT al st.status
    def actualizarStatus(self, msg: str, state: str):
        self.status.write(msg)
        self.status.update(label=msg, state=state)
    
    # Ejecuta el script `download.sh` y captura STDOUT para ponerlo en Streamlit
    def ejecutarDescarga(self):
        # Desempaqueta la lista de las urls
        ydl = subprocess.Popen(stdout=subprocess.PIPE, text=True, args=[self.script, self.uuid, self.fmt, *self.url])

        while (line := ydl.stdout.readline()) != "":
            linea = line.rstrip()
            # Comprobación si no se pudo descargar ningún archivo
            if "FATAL ERROR: No audio files were downloaded." in linea:
                st.session_state['dstate'] = "failed"
                self.eliminarTodo(False)
                return

            # Si una o más canciones no se pudieron descargar, notifica a Streamlit y continúa
            if "ERROR:" in linea and st.session_state['derrors'] == False:
                st.session_state['derrors'] = True

            if "Downloading item " in linea:
                regex = re.search(r'item (\d+) of (\d+)', linea)
                n1 = regex.group(1); n2 = regex.group(2)
                self.actualizarProgreso((float(n1) / float(n2) ), f"Descargando canción {n1} de {n2}...")

            self.actualizarStatus(linea, "running")

            if "Done." in linea:
                self.actualizarStatus(linea, "complete")
                self.actualizarProgreso(100, "Procesando...")
                self.crearZip()
                st.session_state['dstate'] = "finished"
                self.eliminarTodo(True)

    # Guarda la carpeta de descarga en un zip
    def crearZip(self):
        shutil.make_archive(f"./download/{self.uuid}", "zip", f"./download/{self.uuid}")
        self.actualizarStatus("Archivo listo para descarga.", "complete")

    # Elimina la carpeta de antemano y ejecuta en modo detached el script que eliminará el zip después de un tiempo
    def eliminarTodo(self, run_script: bool):
        shutil.rmtree(f"./download/{self.uuid}/")
        if run_script == False: return
        subprocess.Popen(
            preexec_fn = os.setsid,
            args = [self.rmscript, f"./download/{self.uuid}.zip"]
        )