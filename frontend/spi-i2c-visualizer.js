// Визуализация PWM
class PWMVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pwmDevices = {};
        
        if (!this.container) {
            console.error('PWM visualization container not found');
            return;
        }
        
        this.initPWMContainer();
    }
    
    initPWMContainer() {
        this.container.innerHTML = `
            <h3>Управление PWM</h3>
            <div class="pwm-controls" id="pwm-controls"></div>
            <div class="pwm-visualization" id="pwm-visualization"></div>
        `;
    }
    
    addPWM(pin, frequency) {
        const pwmId = `pwm-${pin}`;
        
        // Создаем элемент управления PWM
        const pwmControl = document.createElement('div');
        pwmControl.className = 'pwm-control';
        pwmControl.id = pwmId;
        pwmControl.innerHTML = `
            <div class="pwm-header">
                <h4>PWM Pin ${pin}</h4>
                <span class="pwm-status" id="pwm-status-${pin}">⏹️ Остановлен</span>
            </div>
            <div class="pwm-slider-container">
                <label>Скважность: <span id="pwm-duty-${pin}">0</span>%</label>
                <input type="range" class="pwm-slider" id="pwm-duty-slider-${pin}" 
                       min="0" max="100" value="0">
            </div>
            <div class="pwm-slider-container">
                <label>Частота: <span id="pwm-freq-${pin}">${frequency}</span>Hz</label>
                <input type="range" class="pwm-slider" id="pwm-freq-slider-${pin}" 
                       min="1" max="10000" value="${frequency}" step="10">
            </div>
            <div class="pwm-visual">
                <div class="pwm-wave" id="pwm-wave-${pin}"></div>
            </div>
        `;
        
        document.getElementById('pwm-controls').appendChild(pwmControl);
        
        // Назначаем обработчики слайдеров
        const dutySlider = document.getElementById(`pwm-duty-slider-${pin}`);
        const freqSlider = document.getElementById(`pwm-freq-slider-${pin}`);
        
        dutySlider.addEventListener('input', () => {
            const duty = dutySlider.value;
            document.getElementById(`pwm-duty-${pin}`).textContent = duty;
            this.updatePWMDuty(pin, duty);
            
            // Отправляем команду на изменение скважности
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'pwm_control',
                    pin: pin,
                    duty_cycle: parseInt(duty),
                    action: 'duty_change'
                }));
            }
        });
        
        freqSlider.addEventListener('input', () => {
            const freq = freqSlider.value;
            document.getElementById(`pwm-freq-${pin}`).textContent = freq;
            this.updatePWMFrequency(pin, freq);
            
            // Отправляем команду на изменение частоты
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify({
                    type: 'pwm_control',
                    pin: pin,
                    frequency: parseInt(freq),
                    action: 'freq_change'
                }));
            }
        });
        
        this.pwmDevices[pin] = {
            duty: 0,
            frequency: frequency,
            running: false
        };
    }
    
    updatePWM(pin, duty, frequency) {
        if (this.pwmDevices[pin]) {
            this.pwmDevices[pin].duty = duty;
            this.pwmDevices[pin].frequency = frequency;
            this.pwmDevices[pin].running = true;
            
            // Обновляем UI
            document.getElementById(`pwm-duty-${pin}`).textContent = duty;
            document.getElementById(`pwm-freq-${pin}`).textContent = frequency;
            document.getElementById(`pwm-duty-slider-${pin}`).value = duty;
            document.getElementById(`pwm-freq-slider-${pin}`).value = frequency;
            document.getElementById(`pwm-status-${pin}`).textContent = '▶️ Запущен';
            
            // Обновляем визуализацию волны
            this.updatePWMWave(pin, duty, frequency);
        }
    }
    
    updatePWMDuty(pin, duty) {
        if (this.pwmDevices[pin]) {
            this.pwmDevices[pin].duty = duty;
            document.getElementById(`pwm-duty-${pin}`).textContent = duty;
            document.getElementById(`pwm-duty-slider-${pin}`).value = duty;
            this.updatePWMWave(pin, duty, this.pwmDevices[pin].frequency);
        }
    }
    
    updatePWMFrequency(pin, frequency) {
        if (this.pwmDevices[pin]) {
            this.pwmDevices[pin].frequency = frequency;
            document.getElementById(`pwm-freq-${pin}`).textContent = frequency;
            document.getElementById(`pwm-freq-slider-${pin}`).value = frequency;
            this.updatePWMWave(pin, this.pwmDevices[pin].duty, frequency);
        }
    }
    
    updatePWMWave(pin, duty, frequency) {
        const waveElement = document.getElementById(`pwm-wave-${pin}`);
        if (!waveElement) return;
        
        // Создаем SVG визуализацию PWM волны
        const width = 200;
        const height = 60;
        const period = 1000 / frequency; // период в ms
        
        // Очищаем предыдущую визуализацию
        waveElement.innerHTML = '';
        
        // Создаем SVG элемент
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', width);
        svg.setAttribute('height', height);
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        // Рисуем PWM волну
        const points = [];
        const segments = 4; // количество сегментов для отображения
        
        for (let i = 0; i < segments; i++) {
            const xStart = i * (width / segments);
            const xHigh = xStart + (duty / 100) * (width / segments);
            const xEnd = xStart + (width / segments);
            
            // Высокий уровень
            points.push(`${xStart},${height/2}`);
            points.push(`${xHigh},${height/2}`);
            
            // Низкий уровень
            points.push(`${xHigh},${height-10}`);
            points.push(`${xEnd},${height-10}`);
        }
        
        const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline.setAttribute('points', points.join(' '));
        polyline.setAttribute('fill', 'none');
        polyline.setAttribute('stroke', '#4CAF50');
        polyline.setAttribute('stroke-width', '2');
        
        svg.appendChild(polyline);
        waveElement.appendChild(svg);
    }
    
    removePWM(pin) {
        if (this.pwmDevices[pin]) {
            this.pwmDevices[pin].running = false;
            document.getElementById(`pwm-status-${pin}`).textContent = '⏹️ Остановлен';
        }
    }
}

// Визуализация SPI/I2C устройств
class BusVisualizer {
    constructor(spiContainerId, i2cContainerId) {
        this.spiContainer = document.getElementById(spiContainerId);
        this.i2cContainer = document.getElementById(i2cContainerId);
        this.spiDevices = {};
        this.i2cDevices = {};
        this.i2cOperations = {};
        
        if (!this.spiContainer || !this.i2cContainer) {
            console.error('SPI/I2C containers not found');
            return;
        }
    }
    
    initBusDevices() {
        this.spiContainer.innerHTML = '';
        this.i2cContainer.innerHTML = '';
        
        // Добавляем стандартные SPI устройства
        this.addSPIDevice(0, 0, 'MCP3008 ADC');
        this.addSPIDevice(0, 1, 'WS2812 LED Strip');
        
        // Добавляем стандартные I2C устройства
        this.addI2CDevice(0x76, 'BMP280 Sensor');
        this.addI2CDevice(0x27, 'LCD Display');
        this.addI2CDevice(0x68, 'MPU6050 Gyro');
    }
    
    addSPIDevice(bus, device, type) {
        const id = `spi-${bus}-${device}`;
        const deviceElement = document.createElement('div');
        deviceElement.className = 'bus-device';
        deviceElement.id = id;
        deviceElement.innerHTML = `
            <div class="bus-type">SPI</div>
            <div class="bus-address">Bus ${bus}, Device ${device}</div>
            <div class="device-type">${type}</div>
            <div class="device-operation">Нет операций</div>
            <div class="operation-time"></div>
            <div class="activity-indicator"></div>
        `;
        
        this.spiContainer.appendChild(deviceElement);
        this.spiDevices[id] = deviceElement;
    }
    
    addI2CDevice(address, type) {
        const id = `i2c-${address}`;
        const deviceElement = document.createElement('div');
        deviceElement.className = 'bus-device';
        deviceElement.id = id;
        deviceElement.innerHTML = `
            <div class="bus-type">I2C</div>
            <div class="bus-address">0x${address.toString(16).toUpperCase()}</div>
            <div class="device-type">${type}</div>
            <div class="device-operation">Нет операций</div>
            <div class="operation-time"></div>
            <div class="activity-indicator"></div>
        `;
        
        this.i2cContainer.appendChild(deviceElement);
        this.i2cDevices[id] = deviceElement;
    }
    
    updateSPIActivity(bus, device, active) {
        const id = `spi-${bus}-${device}`;
        const deviceElement = this.spiDevices[id];
        
        if (deviceElement) {
            const indicator = deviceElement.querySelector('.activity-indicator');
            if (indicator) {
                indicator.className = active ? 'activity-indicator active' : 'activity-indicator';
            }
            
            // Мигаем всем элементом при активности
            if (active) {
                deviceElement.style.backgroundColor = 'rgba(76, 175, 80, 0.1)';
                setTimeout(() => {
                    deviceElement.style.backgroundColor = '';
                }, 300);
            }
        }
    }
    
    updateI2CActivity(address, active) {
        const id = `i2c-${address}`;
        const deviceElement = this.i2cDevices[id];
        
        if (deviceElement) {
            const indicator = deviceElement.querySelector('.activity-indicator');
            if (indicator) {
                indicator.className = active ? 'activity-indicator active' : 'activity-indicator';
            }
            
            // Мигаем всем элементом при активности
            if (active) {
                deviceElement.style.backgroundColor = 'rgba(33, 150, 243, 0.1)';
                setTimeout(() => {
                    deviceElement.style.backgroundColor = '';
                }, 300);
            }
        }
    }
    
    updateI2COperation(address, operation, register, value) {
        const id = `i2c-${address}`;
        const deviceElement = this.i2cDevices[id];
        
        if (deviceElement) {
            // Сохраняем последнюю операцию
            this.i2cOperations[address] = {
                operation: operation,
                register: register,
                value: value,
                timestamp: new Date().toLocaleTimeString()
            };
            
            // Обновляем отображение
            const operationElement = deviceElement.querySelector('.device-operation');
            const timeElement = deviceElement.querySelector('.operation-time');
            
            if (operationElement && timeElement) {
                const opText = operation === 'read' ? 'Чтение' : 'Запись';
                operationElement.textContent = 
                    `${opText} регистр 0x${register.toString(16).toUpperCase()}: 0x${value.toString(16).toUpperCase()}`;
                
                timeElement.textContent = this.i2cOperations[address].timestamp;
            }
        }
    }
}

// Инициализация визуализаторов
document.addEventListener('DOMContentLoaded', () => {
    window.busVisualizer = new BusVisualizer('spi-devices', 'i2c-devices');
    window.busVisualizer.initBusDevices();
    
    // Инициализируем PWM визуализатор при переключении на вкладку
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.tab === 'spi-i2c' && !window.pwmVisualizer) {
                window.pwmVisualizer = new PWMVisualizer('pwm-visualization');
            }
        });
    });
    
    console.log('SPI/I2C/PWM visualizers initialized');
});