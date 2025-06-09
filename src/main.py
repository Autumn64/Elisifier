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
import json
import time
import streamlit as st
from downloader import Downloader

# Los `st.columns` que aparentemente están a lo random son 
# en realidad para centrar los elementos en la pantalla.

# El session_state `dstate` tiene cinco valores posibles: `idle`, `downloading`, `finished`,
# `urlerror` y `failed`. Streamlit reacciona de manera distinta a cada `dstate`.

# Adicionalmente, streamlit toma el session_state de la URL de descarga, el formato y el UUID 
# generado para cada descarga individual.

# La idea del campo `accepted` en el archivo de configuración es de poner una palabra clave que
# pueda ser identificada por el programa en la URL, para que así reconozca que se trata de un link
# de YouTube, y así proceda a realizar la descarga.

@st.dialog("Ayuda")
# Cuadro de diálogo que aparece al dar al botón de "Ayuda"
def help_msg():
    st.markdown("### Pon una URL, da click a `Iniciar descarga`, y ¡disfruta!")
    st.markdown("**Elisifier** está basado en `yt-dlp`. Si bien este componente soporta [muchos](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) sitios web distintos, esta app sólo admite links de YouTube por razones de practicidad y complejidad.")
    st.markdown("Los links de Invidious y Piped funcionan (excepto las playlists, que esas no las lee), aunque es posible que alguna instancia no funcione si tiene una URL extraña.")
    st.markdown("**Y recuerda: si no posees tu música al comprarla, entonces piratearla no es robar ;).**")
    st.markdown("**Quienes pierden no son tus artistas favoritos; son las empresas de m... ;)**")
    st.divider()
    st.markdown("**Bajo licencia AGPL v3 o superior. [Ver código fuente](https://codeberg.org/Autumn64/Elisifier)**")

def callback(value: bool):
# Callback de los botones
    st.session_state['drunning'] = value

def banner():
# Muestra el título de la pantalla
    st.markdown("<h2 style='text-align: center; '>Elisifier</h2><br><br>", unsafe_allow_html=True)

def download_menu():
# Función que prepara e inicia la descarga
    if st.session_state['dstate'] == "downloading":
        dProgress = st.progress(0, text="Descargando...")
        dStatus = st.status(label="Descargando. Puede tomar un rato...")

        # Instancia de la clase `Downloader` que realiza las operaciones de descarga
        downloader = Downloader(
            url= st.session_state['durl'],
            fmt = st.session_state['dfmt'] if st.session_state['dfmt'] != "ogg" else "vorbis",
            progress = dProgress,
            status = dStatus,
            script = "./download.sh",
            rmscript = "./rmcache.sh"
        )

        st.session_state['did'] = downloader.getUUID()

        downloader.runDownload()
        del downloader

        st.rerun()

    if st.session_state['dstate'] == 'idle': return

    # Variable del UUID de la descarga
    dId = st.session_state['did']

    if not os.path.isfile(f"./download/{dId}.zip"):
        st.session_state['dstate'] = 'idle'
        return

    st.markdown("<h3 style='text-align: center; '>Canciones procesadas con éxito</h3>", unsafe_allow_html=True)
    if st.session_state['derrors'] == True:
        st.markdown("<h5 style='text-align: center; '>Algunas canciones no se descargaron. Quizás tienen restricción de edad o no están disponibles</h5><br>", unsafe_allow_html=True)
    
    # Botón de descarga basado en el UUID
    with open(f"./download/{dId}.zip", "rb") as f:
        dButton = st.columns([1.5, 1, 1.5])[1].download_button(
            label="Descargar todo",
            data=f,
            file_name=f"{dId}.zip",
            mime="application/zip",
            on_click=callback, 
            args=[False]
        )

def main_menu():
# Despliegue del menú principal
    banner()

    # Comprobación de errores
    if st.session_state['dstate'] == "failed":
        st.error("No se pudieron descargar las canciones. Refresque la página e inténtelo más tarde.")
        return

    if st.columns([2.3, 1, 2.2])[1].button("Ayuda", disabled=st.session_state['drunning']): help_msg()

    url = st.text_input(label="URL de playlists o de videos separadas por espacio", placeholder="https://music.youtube.com/...", disabled=st.session_state['drunning'])
    
    format_combo = st.columns([1.3, 1, 1.5])[1].selectbox(label="Formato", 
                                options=["opus", "ogg", "flac", "mp3", "m4a"], accept_new_options=False, disabled=st.session_state['drunning'])

    sd_button = st.columns([1.5, 1, 1.5])[1].button("Iniciar descarga", disabled=st.session_state['drunning'], on_click=callback, args=[True])

    # Pone en el session_state `urlerror` para saber que streamlit debe mostrar un mensaje de error.
    # Sólo bloquea las URLs si la configuración está activada.
    if sd_button and not any(x in url for x in config['accepted']) and config['block_foreign_urls'] == True:
        st.session_state['dstate'] = "urlerror"
        callback(False)
        st.rerun()
    
    if sd_button:
        st.session_state['derrors'] = False
        st.session_state['dfmt'] = format_combo
        st.session_state['durl'] = url
        st.session_state['dstate'] = "downloading"

    if st.session_state['dstate'] == "urlerror":
        st.error("La URL ingresada no es válida o no es de YouTube.")
    
    if st.session_state['dstate'] in ['downloading', 'finished']:
        download_menu()

if __name__ == "__main__":
    # Carga de configuración
    with open("settings.json", "r") as f:
        config: dict = json.load(f)

    st.set_page_config(
        page_title = "Descargar música de YT Music"
    )

    # Session state de url, formato, chequeo de errores y estado de descarga
    if 'durl' not in st.session_state:
        st.session_state['durl'] = ""
    if 'dfmt' not in st.session_state:
        st.session_state['dfmt'] = ""
    if 'derrors' not in st.session_state:
        st.session_state['derrors'] = False
    if 'dstate' not in st.session_state:
        st.session_state['dstate'] = "idle"
    if 'drunning' not in st.session_state:
        st.session_state['drunning'] = False
    
    main_menu()