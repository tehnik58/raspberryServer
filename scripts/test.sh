# Запуск сервера
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Тестирование в другом терминале
python -c "
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8000/api/ws/test-client') as ws:
        # Отправка тестового кода
        code = '''
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

try:
    for i in range(3):
        GPIO.output(18, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(18, GPIO.LOW)
        time.sleep(0.5)
finally:
    GPIO.cleanup()
'''
        await ws.send(json.dumps({'type': 'code_execution', 'code': code}))
        
        # Получение ответов
        for i in range(10):
            response = await ws.recv()
            data = json.loads(response)
            print(f'{data[\"type\"]}: {data.get(\"message\", \"\")}')

asyncio.run(test())
"