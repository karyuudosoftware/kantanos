#!/bin/bash
# crop.sh <shot-name> <WxH+X+Y> [scale%] — writes output/shots/<name>-crop.png for a closer look.
S=/mnt/d/CLAUDE_Projects/kantanos/output/shots
magick "$S/$1.png" -crop "$2" +repage -filter point -resize "${3:-200}%" "$S/$1-crop.png" && echo "saved $1-crop.png"
