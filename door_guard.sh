#!/bin/bash

COUNT=$(ps -ef | grep "device_126.py" | grep -v "grep" | wc -l)

if [[ ${COUNT} -eq 0 ]]
then
    nohup /usr/bin/python3 /home/pi/door/device_126.py > /dev/null 2>&1 &
fi

COUNT=$(ps -ef | grep "device_128.py" | grep -v "grep" | wc -l)

if [[ ${COUNT} -eq 0 ]]
then
    nohup /usr/bin/python3 /home/pi/door/device_128.py > /dev/null 2>&1 &
fi
