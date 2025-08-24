// Визуализация GPIO пинов
class GPIOVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.pins = {};
        this.initGPIOComponents();
    }

    initGPIOComponents() {
        // Очищаем контейнер
        this.container.innerHTML = '';
        
        // Создаем визуальные элементы для GPIO пинов (только основные пины)
        const importantPins = [2, 3, 4, 14, 15, 17, 18, 27, 22, 23, 24, 10, 9, 25, 11, 8, 7];
        
        for (let pin of importantPins) {
            const pinElement = document.createElement('div');
            pinElement.className = 'gpio-pin gpio-inactive';
            pinElement.id = `gpio-${pin}`;
            pinElement.innerHTML = `<span>${pin}</span>`;
            
            this.container.appendChild(pinElement);
            this.pins[pin] = pinElement;
        }
    }

    updatePinState(pin, state) {
        const pinElement = this.pins[pin];
        if (pinElement) {
            if (state) {
                pinElement.classList.remove('gpio-inactive');
                pinElement.classList.add('gpio-active');
            } else {
                pinElement.classList.remove('gpio-active');
                pinElement.classList.add('gpio-inactive');
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