#!/bin/bash

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

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "Usage: './download.sh <folder> <format> <youtube_links>'"
  exit 1
fi

# Carpeta de trabajo
cd download
mkdir -p "$1"
cd "$1"

# URL de la playlist
playlist_url="$3"

# Formato
fmt="$2"

# Descarga audio + miniatura + metadatos
if ! yt-dlp -f "bestaudio/best" \
  -o "%(playlist_index)s %(channel)s - %(title)s.%(ext)s" \
  -x --audio-format "$fmt" --audio-quality 0 \
  --embed-thumbnail --embed-metadata \
  --write-thumbnail --convert-thumbnails jpg \
  "$playlist_url" ; then
  echo "Error downloading"
  exit 1
fi

if [ $fmt == "vorbis" ]; then
  fmt="ogg"
fi

# Procesa cada imagen descargada
for img in *.jpg; do
  # Recorta imagen a cuadrado centrado
  magick "$img" -gravity center -crop 1:1 +repage "$img"
done

# Reemplaza miniaturas en los archivos de audio con las cuadradas
for audio in *."$fmt"; do
  # Busca miniatura correspondiente
  base="${audio%.*}"
  square_img=$(ls "${base}"*.jpg 2>/dev/null | head -n 1)

  if [[ -f "$square_img" ]]; then
    echo "Adding cover to $audio"
    # Añade imagen como portada
    if ! kid3-cli -c "set picture:\"$square_img\" ''" "$audio" ; then
      echo "Error addign $square_img to $audio"
    fi
  else
    echo "Couldn't find any cover art for $audio"
  fi
done

rm *.jpg

echo "Done."
