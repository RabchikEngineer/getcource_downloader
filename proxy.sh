#!/usr/bin/bash
source ../.venv/bin/activate

mitmdump -p 8080 -s proxy_interceptor.py
