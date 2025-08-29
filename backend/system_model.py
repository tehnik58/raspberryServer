# backend/system_model.py
import asyncio
import json
import os
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

# --- Интерфейсы и типы ---

class ComponentType(Enum):
    GPIO = "gpio"
    MOTOR = "motor"
    STEPPER = "stepper"
    SENSOR = "sensor"
    LCD = "lcd"
    LED = "led"
    BUTTON = "button"
    ADC = "adc"

@dataclass
class Connection:
    from_component: str  # например, "GPIO18"
    to_component: str    # например, "LED1"
    type: str = "wire"   # тип соединения

# --- Основной класс модели системы ---

class SystemModel:
    def __init__(self):
        self.components: Dict[str, Dict] = {}
        self.connections: List[Connection] = []
        self.event_callbacks: Dict[str, List[Callable]] = {}
        self.state_file = "/app/system_state.json"
        self._lock = asyncio.Lock()
        self._running = True
        self._task = None
        self._load_state()

    def _load_state(self):
        """Загружает сохранённое состояние системы (если есть)"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.components = data.get("components", {})
                    self.connections = [Connection(**c) for c in data.get("connections", [])]
            except Exception as e:
                print(f"Failed to load system state: {e}")

    def _save_state(self):
        """Сохраняет состояние системы"""
        try:
            data = {
                "components": self.components,
                "connections": [c.__dict__ for c in self.connections]
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save system state: {e}")

    # --- Управление компонентами ---

    def add_component(self, id: str, type: ComponentType, **kwargs):
        """Добавляет компонент в систему"""
        self.components[id] = {
            "id": id,
            "type": type.value,
            "state": kwargs.get("state", {}),
            "config": kwargs.get("config", {}),
            "meta": kwargs.get("meta", {})
        }
        self._fire_event("component_added", {"id": id, "type": type.value})
        self._save_state()

    def remove_component(self, id: str):
        """Удаляет компонент и все его соединения"""
        if id in self.components:
            del self.components[id]
            self.connections = [c for c in self.connections if c.from_component != id and c.to_component != id]
            self._fire_event("component_removed", {"id": id})
            self._save_state()

    def update_component_state(self, id: str, **state):
        """Обновляет состояние компонента"""
        if id in self.components:
            self.components[id]["state"].update(state)
            self._fire_event("state_update", {
                "id": id,
                "type": self.components[id]["type"],
                "state": self.components[id]["state"]
            })
            # Проверяем, как компоненты связаны
            self._propagate_signal(id, state)

    def get_component(self, id: str) -> Optional[Dict]:
        return self.components.get(id)

    # --- Управление соединениями ---

    def connect(self, from_id: str, to_id: str, type: str = "wire"):
        """Соединяет два компонента"""
        if from_id not in self.components or to_id not in self.components:
            raise ValueError("Component not found")
        conn = Connection(from_component=from_id, to_component=to_id, type=type)
        self.connections.append(conn)
        self._fire_event("connection_added", {
            "from": from_id,
            "to": to_id,
            "type": type
        })
        self._save_state()

    def disconnect(self, from_id: str, to_id: str):
        """Удаляет соединение"""
        self.connections = [c for c in self.connections if not (c.from_component == from_id and c.to_component == to_id)]
        self._fire_event("connection_removed", {"from": from_id, "to": to_id})
        self._save_state()

    # --- Пропагация сигналов (важно!) ---

    def _propagate_signal(self, source_id: str, state: Dict):
        """Распространяет сигнал по схеме"""
        for conn in self.connections:
            if conn.from_component == source_id:
                target = self.components.get(conn.to_component)
                if not target:
                    continue
                # Пример: если GPIO18 (HIGH) → LED1, то включаем LED
                if target["type"] == "led":
                    led_state = bool(state.get("value", False))
                    self.update_component_state(conn.to_component, on=led_state)
                elif target["type"] == "motor":
                    speed = state.get("value", 0) * 100  # 0-1 → 0-100%
                    self.update_component_state(conn.to_component, speed=speed, running=True)
                # Другие правила...

    # --- События и подписки ---

    def on(self, event: str, callback: Callable):
        """Подписка на событие"""
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        self.event_callbacks[event].append(callback)

    def _fire_event(self, event: str, data: Dict):
        """Генерирует событие"""
        if event in self.event_callbacks:
            for cb in self.event_callbacks[event]:
                try:
                    cb(event, data)
                except Exception as e:
                    print(f"Event callback error: {e}")

    # --- Цикл обновления (для датчиков и физики) ---

    async def start_update_loop(self):
        """Запускает фоновый цикл обновления (датчики, моторы и т.д.)"""
        while self._running:
            await asyncio.sleep(0.1)
            async with self._lock:
                self._update_sensors()
                self._update_motors()

    def _update_sensors(self):
        """Имитирует изменение датчиков"""
        for cid, comp in self.components.items():
            if comp["type"] == "sensor":
                sensor_type = comp["config"].get("sensor_type")
                current = comp["state"].get("value", 25.0)
                if sensor_type == "temperature":
                    new_val = current + random.uniform(-0.2, 0.2)
                    self.update_component_state(cid, value=round(new_val, 2))
                elif sensor_type == "distance":
                    new_val = random.uniform(5, 50)
                    self.update_component_state(cid, value=round(new_val, 2))

    def _update_motors(self):
        """Обновляет состояние моторов"""
        for cid, comp in self.components.items():
            if comp["type"] == "motor" and comp["state"].get("running"):
                speed = comp["state"]["speed"]
                pos = comp["state"].get("position", 0)
                new_pos = pos + speed * 0.1  # интегрируем
                self.update_component_state(cid, position=new_pos)

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def start(self):
        """Запускает фоновый процесс обновления"""
        self._task = asyncio.create_task(self.start_update_loop())