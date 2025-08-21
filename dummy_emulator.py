#!/usr/bin/env python3
"""
Простой скрипт для поддержания контейнера активным
На следующем этапе будет заменен на полноценный демон
"""

import time
import os

print("Virtual Constructor Emulator Container started")
print(f"Session ID: {os.environ.get('SESSION_ID', 'unknown')}")

# Бесконечный цикл для поддержания контейнера активным
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("Container stopping...")