#!/bin/bash

COUNT=$(ps -ef | grep "door.py" | grep -v "grep" | wc -l)

if [[ ${COUNT} -eq 0 ]]
then
    nohup /home/xwq/src/door/venv/bin/python /home/xwq/src/door/door.py > /dev/null 2>&1 &
fi