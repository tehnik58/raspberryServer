// Визуализация GPIO пинов
class GPIOVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pins = {};
        this.pinModes = {};
        this.initGPIOComponents();
    }
    
    initGPIOComponents() {
        this.container.innerHTML = '';
        
        const importantPins = [2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24, 10, 9, 25, 11, 8, 7];
        
        for (let pin of importantPins) {
            const pinElement = document.createElement('div');
            pinElement.className = 'gpio-pin gpio-inactive';
            pinElement.id = `gpio-${pin}`;
            pinElement.innerHTML = `
                <span>${pin}</span>
                <div class="pin-mode">OUT</div>
            `;
            
            // Добавляем обработчик клика
            pinElement.addEventListener('click', () => {
                this.togglePinState(pin);
            });
            
            this.container.appendChild(pinElement);
            this.pins[pin] = pinElement;
            this.pinModes[pin] = 'out'; // По умололчанию выход
        }
    }
    
    setPinMode(pin, mode) {
        this.pinModes[pin] = mode;
        const pinElement = this.pins[pin];
        
        if (pinElement) {
            const modeElement = pinElement.querySelector('.pin-mode');
            if (modeElement) {
                modeElement.textContent = mode.toUpperCase();
            }
            
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
    
    updatePWMState(pin, duty_cycle, frequency) {
        const pinElement = this.pins[pin];
        
        if (pinElement) {
            // Обновляем отображение PWM
            const intensity = 0.5 + (duty_cycle / 200);
            pinElement.style.opacity = intensity;
            
            // Обновляем подсказку
            pinElement.title = `PWM: ${duty_cycle}% @ ${frequency}Hz`;
            
            // Добавляем анимацию мерцания для PWM
            if (duty_cycle > 0 && duty_cycle < 100) {
                pinElement.style.animation = `pwm-flicker ${1/frequency}s infinite`;
            } else {
                pinElement.style.animation = 'none';
            }
            
            // Обновляем текст режима
            const modeElement = pinElement.querySelector('.pin-mode');
            if (modeElement) {
                modeElement.textContent = `PWM ${duty_cycle}%`;
            }
        }
    }
    
    resetAllPins() {
        for (let pin in this.pins) {
            this.updatePinState(parseInt(pin), false);
            this.setPinMode(parseInt(pin), 'out');
        }
    }
}

// Визуализация моторов
class MotorVisualizer {
    constructor(controlContainerId, visualContainerId) {
        this.controlContainer = document.getElementById(controlContainerId);
        this.visualContainer = document.getElementById(visualContainerId);
        this.motors = {};
    }
    
    initMotorControls() {
        this.controlContainer.innerHTML = '';
        this.visualContainer.innerHTML = '';
        
        // Создаем контролы для двух моторов
        this.createMotorControl('left_motor', 'Левый мотор');
        this.createMotorControl('right_motor', 'Правый мотор');
        
        // Создаем визуализацию для шагового мотора
        this.createStepperControl('stepper', 'Шаговый мотор');
    }
    
    createMotorControl(name, label) {
        const motorControl = document.createElement('div');
        motorControl.className = 'motor-control';
        motorControl.innerHTML = `
            <h3>${label}</h3>
            <div class="motor-slider-container">
                <input type="range" class="motor-slider" id="${name}-slider" 
                       min="-100" max="100" value="0">
                <span id="${name}-value">0%</span>
            </div>
            <div class="motor-direction">
                <button class="dir-btn" data-motor="${name}" data-dir="-1">◀️ Назад</button>
                <button class="stop-btn" data-motor="${name}">⏹️ Стоп</button>
                <button class="dir-btn" data-motor="${name}" data-dir="1">Вперед ▶️</button>
            </div>
            <div class="motor-visual">
                <div class="motor-rotation" id="${name}-visual"></div>
            </div>
        `;
        
        this.controlContainer.appendChild(motorControl);
        
        // Назначаем обработчики
        const slider = document.getElementById(`${name}-slider`);
        const valueDisplay = document.getElementById(`${name}-value`);
        
        slider.addEventListener('input', () => {
            const speed = parseInt(slider.value);
            valueDisplay.textContent = `${speed}%`;
            this.updateMotor(name, speed, speed >= 0 ? 1 : -1);
            
            // Отправляем на сервер
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'motor_control',
                    name: name,
                    speed: speed
                }));
            }
        });
        
        // Обработчики для кнопок направления
        const dirButtons = motorControl.querySelectorAll('.dir-btn');
        dirButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const dir = parseInt(btn.dataset.dir);
                const speed = dir * 50; // 50% скорости в выбранном направлении
                slider.value = speed;
                valueDisplay.textContent = `${speed}%`;
                this.updateMotor(name, speed, dir);
                
                // Отправляем на сервер
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(JSON.stringify({
                        type: 'motor_control',
                        name: name,
                        speed: speed
                    }));
                }
            });
        });
        
        // Обработчик для кнопки остановки
        const stopBtn = motorControl.querySelector('.stop-btn');
        stopBtn.addEventListener('click', () => {
            slider.value = 0;
            valueDisplay.textContent = '0%';
            this.updateMotor(name, 0, 1);
            
            // Отправляем на сервер
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'motor_control',
                    name: name,
                    speed: 0
                }));
            }
        });
        
        this.motors[name] = {
            speed: 0,
            direction: 1
        };
    }
    
    createStepperControl(name, label) {
        const stepperControl = document.createElement('div');
        stepperControl.className = 'motor-control';
        stepperControl.innerHTML = `
            <h3>${label}</h3>
            <div class="stepper-controls">
                <button class="stepper-btn" data-steps="-100">-100</button>
                <button class="stepper-btn" data-steps="-10">-10</button>
                <button class="stepper-btn" data-steps="-1">-1</button>
                <span id="stepper-position">0</span>
                <button class="stepper-btn" data-steps="1">+1</button>
                <button class="stepper-btn" data-steps="10">+10</button>
                <button class="stepper-btn" data-steps="100">+100</button>
            </div>
            <div class="motor-visual">
                <div class="stepper-visual" id="stepper-visual"></div>
            </div>
        `;
        
        this.controlContainer.appendChild(stepperControl);
        
        // Обработчики для кнопок шагового мотора
        const stepperButtons = stepperControl.querySelectorAll('.stepper-btn');
        stepperButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const steps = parseInt(btn.dataset.steps);
                
                // Отправляем на сервер
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                    websocket.send(JSON.stringify({
                        type: 'stepper_control',
                        name: name,
                        steps: steps
                    }));
                }
            });
        });
    }
    
    updateMotor(name, speed, direction) {
        if (this.motors[name]) {
            this.motors[name].speed = speed;
            this.motors[name].direction = direction;
            
            // Обновляем визуализацию
            const visual = document.getElementById(`${name}-visual`);
            if (visual) {
                // Устанавливаем скорость вращения
                const absSpeed = Math.abs(speed);
                const rotationSpeed = 3 - (absSpeed / 100 * 2.8); // От 0.2s до 3s
                
                if (absSpeed > 0) {
                    visual.style.animation = `rotate ${rotationSpeed}s linear infinite`;
                    visual.style.animationDirection = direction > 0 ? 'normal' : 'reverse';
                } else {
                    visual.style.animation = 'none';
                }
            }
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
    window.motorVisualizer = new MotorVisualizer('motor-controls', 'motor-visualization');
    window.sensorVisualizer = new SensorVisualizer('sensor-data');
    
    console.log('Components initialized');
});