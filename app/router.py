import asyncio
from http.client import HTTPException
import re
from typing import Any, Dict
from app.Emulator.Emulate import EmulatedGPIO
from fastapi import FastAPI, WebSocket, UploadFile
from pydantic import BaseModel
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

@app.post("/api/execute")
async def execute_code(request: CodeExecutionRequest) -> Dict[str, Any]:
    # 1. Валидация кода
    if not await validate_code(request.code):
        raise HTTPException(status_code=400, detail="Код содержит запрещённые операторы")

    # 2. Инициализация эмулятора GPIO
    if not isinstance(request.hardware_config.get("gpio"), dict):
        raise HTTPException(
            status_code=400,
            detail="hardware_config['gpio'] должен быть словарём (например: {'17': 'OUT', '18': 'IN'})"
        )

    # 2. Проверяем, что все пины — числа
    try:
        pin_config = {
            int(pin): mode  # Преобразуем номер пина в int
            for pin, mode in request.hardware_config["gpio"].items()
        }
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Номера пинов должны быть числами (например '17', а не 'gpio')"
        )

    # 3. Инициализируем GPIOEmulator с валидными данными
    gpio_emulator = GPIOEmulator(pin_config)

    # 3. Подготовка контекста выполнения
    execution_context = {
        "GPIO": gpio_emulator,
        "__builtins__": {
            "range": range,
            "print": print,
            "len": len,
            "sleep": asyncio.sleep,
            "Exception": Exception
        }
    }

    # 4. Захват вывода (stdout)
    output_buffer = []
    original_print = print
    def custom_print(*args, **kwargs):
        output_buffer.append(" ".join(map(str, args)))
        original_print(*args, **kwargs)
    execution_context["print"] = custom_print

    # 5. Выполнение кода с таймаутом
    try:
        await asyncio.wait_for(
            async_exec_code(request.code, execution_context),
            timeout=5.0  # Максимум 5 секунд на выполнение
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Превышено время выполнения")
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "gpio_state": gpio_emulator.get_state(),
            "output": "\n".join(output_buffer)
        }

    # 6. Возврат результата
    return {
        "status": "success",
        "gpio_state": gpio_emulator.get_state(),
        "output": "\n".join(output_buffer),
        "error": None
    }

async def async_exec_code(code: str, context: Dict) -> None:
    """Асинхронное выполнение кода через exec"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: exec(code, context))

async def validate_code(code: str) -> bool:
    """Проверяет код на запрещённые конструкции"""
    banned_patterns = [
        r"import\s+os\b",
        r"__import__\(",
        r"open\(",
        r"eval\(",
        r"subprocess\b"
    ]
    return not any(re.search(pattern, code) for pattern in banned_patterns)

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

class GPIOEmulator:
    """Эмулятор GPIO Raspberry Pi"""
    def __init__(self, pin_config: Dict[str, str]):
        self.pins = {}
        for pin, mode in pin_config.items():
            self.setup(int(pin), mode)

    def setup(self, pin: int, mode: str):
        """Настройка режима пина (IN/OUT)"""
        self.pins[pin] = {"mode": mode, "value": 0}

    def output(self, pin: int, value: int):
        """Установка значения выхода"""
        if pin not in self.pins or self.pins[pin]["mode"] != "OUT":
            raise RuntimeError(f"Pin {pin} не настроен как OUTPUT")
        self.pins[pin]["value"] = value

    def input(self, pin: int) -> int:
        """Чтение значения входа"""
        if pin not in self.pins or self.pins[pin]["mode"] != "IN":
            raise RuntimeError(f"Pin {pin} не настроен как INPUT")
        return self.pins[pin].get("value", 0)

    def get_state(self) -> Dict[str, Dict]:
        """Возвращает текущее состояние всех пинов"""
        return {str(pin): data for pin, data in self.pins.items()}