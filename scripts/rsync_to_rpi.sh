#!/bin/bash

rsync -av \
      --delete \
      --exclude=.git \
      --exclude=.idea \
      --exclude=*.db \
      . pi@192.168.100.28:/home/pi/weather-station
