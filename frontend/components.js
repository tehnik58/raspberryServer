// Визуализация GPIO пинов
class GPIOVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pins = {};
        this.pinModes = {}; // Хранение режимов пинов
        this.initGPIOComponents();
    }

    updatePWMState(pin, duty_cycle, frequency) {
        const pinElement = this.pins[pin];
        if (pinElement) {
            // Обновляем отображение PWM
            pinElement.style.opacity = 0.5 + (duty_cycle / 200); // Визуальная индикация
            pinElement.title = `PWM: ${duty_cycle}% @ ${frequency}Hz`;

            // Добавляем анимацию мерцания для PWM
            if (duty_cycle > 0 && duty_cycle < 100) {
                pinElement.style.animation = `pwm-flicker ${1/frequency}s infinite`;
            } else {
                pinElement.style.animation = 'none';
            }
        }
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
class MotorVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.motors = {};
    }
    
    addMotor(name, maxSpeed = 100) {
        const motorElement = document.createElement('div');
        motorElement.className = 'motor';
        motorElement.innerHTML = `
            <div class="motor-name">${name}</div>
            <div class="motor-speed">0%</div>
            <div class="motor-direction">▶️</div>
            <div class="motor-bar">
                <div class="motor-progress"></div>
            </div>
        `;
        
        this.container.appendChild(motorElement);
        this.motors[name] = motorElement;
    }
    
    updateMotor(name, speed, direction) {
        const motor = this.motors[name];
        if (motor) {
            const speedElement = motor.querySelector('.motor-speed');
            const directionElement = motor.querySelector('.motor-direction');
            const progressElement = motor.querySelector('.motor-progress');
            
            speedElement.textContent = `${Math.abs(speed)}%`;
            directionElement.textContent = speed >= 0 ? '▶️' : '◀️';
            
            // Анимация скорости
            progressElement.style.width = `${Math.abs(speed)}%`;
            progressElement.style.background = speed >= 0 ? '#4CAF50' : '#f44336';
        }
    }
}

// Добавить CSS стили для моторов и PWM
const motorStyles = `
.motor {
    border: 2px solid #ddd;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
    background: white;
}

.motor-name {
    font-weight: bold;
    margin-bottom: 5px;
}

.motor-speed {
    font-size: 18px;
    font-weight: bold;
    color: #333;
}

.motor-direction {
    font-size: 24px;
    text-align: center;
    margin: 5px 0;
}

.motor-bar {
    width: 100%;
    height: 20px;
    background: #f0f0f0;
    border-radius: 10px;
    overflow: hidden;
}

.motor-progress {
    height: 100%;
    width: 0%;
    transition: width 0.3s ease;
    border-radius: 10px;
}

@keyframes pwm-flicker {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
}
`;

// Добавить стили в документ
const styleSheet = document.createElement('style');
styleSheet.textContent = motorStyles;
document.head.appendChild(styleSheet);

// Инициализация компонентов после загрузки страницы
document.addEventListener('DOMContentLoaded', () => {
    window.gpioVisualizer = new GPIOVisualizer('gpio-components');
    window.sensorVisualizer = new SensorVisualizer('sensor-data');
    console.log('Components initialized');
});