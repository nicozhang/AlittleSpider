#!/bin/bash
ps aux|grep scope | awk '{print $2}'|xargs kill -9
nohup ./venv3.4/bin/python ./foobar/china_scope_finance_spider.py production > out_finance.txt 2>&1 &
nohup ./venv3.4/bin/python ./foobar/china_scope_spider.py production > out.txt 2>&1 &
