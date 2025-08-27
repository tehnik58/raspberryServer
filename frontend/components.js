// Визуализация GPIO пинов
class GPIOVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pins = {};
        this.pinModes = {}; // Хранение режимов пинов
        this.initGPIOComponents();
    }

    initGPIOComponents() {
        this.container.innerHTML = '';
        const importantPins = [2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24, 10, 9, 25, 11, 8, 7];

        for (let pin of importantPins) {
            const pinElement = document.createElement('div');
            pinElement.className = 'gpio-pin gpio-inactive';
            pinElement.id = `gpio-${pin}`;
            pinElement.innerHTML = `<span>${pin}</span>`;
            
            // Добавляем обработчик клика
            pinElement.addEventListener('click', () => {
                this.togglePinState(pin);
            });
            
            this.container.appendChild(pinElement);
            this.pins[pin] = pinElement;
            this.pinModes[pin] = 'out'; // По умолчанию выход
        }
    }

    setPinMode(pin, mode) {
        this.pinModes[pin] = mode;
        const pinElement = this.pins[pin];
        if (pinElement) {
            if (mode === 'in') {
                pinElement.classList.add('gpio-input');
                pinElement.classList.remove('gpio-output');
            } else {
                pinElement.classList.add('gpio-output');
                pinElement.classList.remove('gpio-input');
            }
        }
    }

    togglePinState(pin) {
        if (this.pinModes[pin] === 'in') {
            const currentState = this.pins[pin].classList.contains('gpio-active');
            const newState = !currentState;
            
            this.updatePinState(pin, newState, 'input');
            
            // Отправляем изменение состояния на сервер
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'gpio_input',
                    pin: pin,
                    state: newState
                }));
            }
        }
    }

    updatePinState(pin, state, mode = 'output') {
        const pinElement = this.pins[pin];
        if (pinElement) {
            if (state) {
                pinElement.classList.remove('gpio-inactive');
                pinElement.classList.add('gpio-active');
            } else {
                pinElement.classList.remove('gpio-active');
                pinElement.classList.add('gpio-inactive');
            }
            
            // Обновляем режим если передан
            if (mode) {
                this.setPinMode(pin, mode);
            }
        }
    }

    resetAllPins() {
        for (let pin in this.pins) {
            this.updatePinState(pin, false);
        }
    }
}

// Визуализация данных с датчиков
class SensorVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.sensors = {};
    }

    updateSensorValue(sensorName, value, unit = '') {
        if (!this.sensors[sensorName]) {
            const sensorElement = document.createElement('div');
            sensorElement.className = 'sensor-value';
            sensorElement.id = `sensor-${sensorName}`;
            this.container.appendChild(sensorElement);
            this.sensors[sensorName] = sensorElement;
        }

        this.sensors[sensorName].textContent = `${sensorName}: ${value} ${unit}`;
    }
}

// Инициализация компонентов после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
    window.gpioVisualizer = new GPIOVisualizer('gpio-components');
    window.sensorVisualizer = new SensorVisualizer('sensor-data');
    console.log('Components initialized');
});