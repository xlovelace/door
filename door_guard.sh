#!/bin/bash

COUNT=$(ps -ef | grep "device_126.py" | grep -v "grep" | wc -l)

if [[ ${COUNT} -eq 0 ]]
then
    nohup /home/xwq/src/door/venv/bin/python /home/xwq/src/door/door.py > /dev/null 2>&1 &
fi

COUNT=$(ps -ef | grep "device_128.py" | grep -v "grep" | wc -l)

if [[ ${COUNT} -eq 0 ]]
then
    nohup /home/xwq/src/door/venv/bin/python /home/xwq/src/door/door.py > /dev/null 2>&1 &
fi
