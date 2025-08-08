import asyncio
from http.client import HTTPException
import math
import random
import re
import time
from typing import Any, Dict
from app.Emulator.Emulate import EmulatedGPIO, GPIOEmulator
from fastapi import FastAPI, WebSocket, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from types import FunctionType
import docker

app = FastAPI()
client = docker.from_env()

# Модели запросов
class CodeExecutionRequest(BaseModel):
    code: str
    hardware_config: dict  # GPIO настройки и т.д.

# Хранилище состояний
sessions = {}

def execute_user_code(code: str, gpio: EmulatedGPIO):
    locals_dict = {"GPIO": gpio}
    try:
        exec(code, {"__builtins__": None}, locals_dict)
    except Exception as e:
        return {"error": str(e)}
    return gpio.get_state()

def create_safe_context(gpio_emulator):
    """Создает максимально полный и безопасный контекст выполнения"""
    
    # Базовые безопасные типы и функции
    safe_builtins = {
        # Основные встроенные функции
        'print': print,
        'range': range,
        'len': len,
        'repr': repr,
        'enumerate': enumerate,
        'isinstance': isinstance,
        'issubclass': issubclass,
        'callable': callable,
        'hasattr': hasattr,
        'getattr': getattr,
        'setattr': setattr,
        'property': property,
        'staticmethod': staticmethod,
        'classmethod': classmethod,
        
        # Базовые типы
        'bool': bool,
        'int': int,
        'float': float,
        'str': str,
        'list': list,
        'tuple': tuple,
        'dict': dict,
        'set': set,
        'frozenset': frozenset,
        
        # Исключения
        'Exception': Exception,
        'ValueError': ValueError,
        'TypeError': TypeError,
        
        # Критически важные для ООП
        '__build_class__': __build_class__,
        '__name__': '__main__',
        '__file__': '<virtual>',
        '__debug__': False,
        
        # Контролируемый импорт
        '__import__': create_importer(['math', 'random', 'time'])
    }
    
    # Специальные объекты для работы с GPIO
    gpio_objects = {
        'GPIO': gpio_emulator,
        'sleep': safe_sleep,
        'time': {
            'sleep': safe_sleep,
            'time': time.time
        }
    }
    
    # Модули для математических операций
    math_module = {
        'sin': math.sin,
        'cos': math.cos,
        'pi': math.pi,
        'sqrt': math.sqrt,
        # ... другие безопасные математические функции
    }
    
    # Собираем полный контекст
    context = {
        '__builtins__': safe_builtins,
        **gpio_objects,
        'math': math_module,
        'random': {
            'random': random.random,
            'randint': random.randint,
            'choice': random.choice
        },
        # Механизм для отладки
        '__debug_tools__': {
            'vars': lambda: {k: v for k, v in context.items() if not k.startswith('_')},
            'gpio_state': lambda: gpio_emulator.get_state()
        }
    }
    
    # Добавляем себя в контекст для рекурсивного доступа
    context['__context__'] = context
    
    return context

def create_importer(allowed_modules):
    """Создает безопасную функцию импорта"""
    def safe_importer(name, globals=None, locals=None, fromlist=(), level=0):
        if name not in allowed_modules:
            raise ImportError(f"Module {name} is not allowed")
        return __import__(name, globals, locals, fromlist, level)
    return safe_importer

def safe_sleep(seconds):
    """Защищенная функция sleep"""
    if not isinstance(seconds, (int, float)):
        raise TypeError("Sleep duration must be a number")
    if seconds < 0:
        raise ValueError("Sleep duration must be non-negative")
    if seconds > 10:  # Максимум 10 секунд
        seconds = 10
    time.sleep(seconds)

@app.post("/api/execute")
async def execute_code(request: CodeExecutionRequest):
    try:
        # Инициализация
        gpio_emulator = GPIOEmulator(request.hardware_config.get("gpio", {}))
        context = create_safe_context(gpio_emulator)
        
        # Перехват вывода
        output_buffer = []
        context["print"] = lambda *args: output_buffer.append(" ".join(map(str, args)))
        context["__builtins__"]["staticmethod"] = staticmethod
        context["__builtins__"]["classmethod"] = classmethod
        context["__builtins__"]["property"] = property
        
        # Выполнение
        start_time = time.time()
        await asyncio.wait_for(
            run_in_executor(request.code, context),
            timeout=30.0
        )
        
        return {
            "status": "success",
            "gpio_state": gpio_emulator.get_state(),
            "output": "\n".join(output_buffer),
            "execution_time": round(time.time() - start_time, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def run_in_executor(code, context):
    """Асинхронное выполнение кода"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: exec(code, context))

async def run_in_executor(code, context):
    """Запуск кода в отдельном потоке"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: exec(code, context))

@app.get("/api/hardware_state/{session_id}")
async def get_hardware_state(session_id: str):
    """Получение текущего состояния GPIO/датчиков"""
    return sessions.get(session_id, {})

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для реального времени"""
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        # Обработка в реальном времени...