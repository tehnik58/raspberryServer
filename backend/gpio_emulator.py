from typing import Dict

class GPIOEmulator:
    def __init__(self):
        self.pin_states: Dict[int, bool] = {}
    
    def update_pin_state(self, pin: int, state: bool):
        """Обновляет состояние GPIO пина"""
        self.pin_states[pin] = state
    
    def get_pin_state(self, pin: int) -> bool:
        """Возвращает состояние GPIO пина"""
        return self.pin_states.get(pin, False)
    
    def reset_all_pins(self):
        """Сбрасывает все пины в неактивное состояние"""
        self.pin_states.clear()