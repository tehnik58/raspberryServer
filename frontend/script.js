document.addEventListener('DOMContentLoaded', function() {
    console.log('Документ загружен, инициализируем приложение...');
    
    // Получаем элементы DOM
    const codeTextarea = document.getElementById('python-code');
    const runButton = document.getElementById('run-btn');
    const stopButton = document.getElementById('stop-btn');
    const clearButton = document.getElementById('clear-btn');
    const saveButton = document.getElementById('save-btn');
    const loadButton = document.getElementById('load-btn');
    const themeToggle = document.getElementById('theme-toggle');
    const helpBtn = document.getElementById('help-btn');
    const outputConsole = document.getElementById('output-console');
    const statusElement = document.getElementById('status');
    const connectionTimeElement = document.getElementById('connection-time');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const modal = document.getElementById('help-modal');
    const closeModal = document.querySelector('.close');
    
    let websocket = null;
    let connectionStartTime = null;
    let connectionTimer = null;
    const serverUrl = 'ws://' + window.location.hostname + ':8000/ws/execute';
    
    // Инициализация темы
    const currentTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    themeToggle.textContent = currentTheme === 'light' ? '🌙 Тёмная' : '☀️ Светлая';
    
    // Инициализация компонентов
    if (window.gpioVisualizer) {
        window.gpioVisualizer.initGPIOComponents();
    }
    
    if (window.motorVisualizer) {
        window.motorVisualizer.initMotorControls();
    }
    
    if (window.busVisualizer) {
        window.busVisualizer.initBusDevices();
    }
    
    // Обработчик сообщений от сервера
    function handleWebSocketMessage(message) {
        switch (message.type) {
            case 'output':
                addMessage(message.content);
                detectHardwareEvents(message.content);
                break;
                
            case 'error':
                addMessage(`❌ Ошибка: ${message.content}`, 'error');
                break;
                
            case 'execution_started':
                addMessage('🚀 Выполнение началось');
                runButton.disabled = true;
                if (window.gpioVisualizer) {
                    window.gpioVisualizer.resetAllPins();
                }
                break;
                
            case 'execution_completed':
                addMessage('✅ Выполнение завершено');
                runButton.disabled = false;
                break;
                
            case 'gpio_state_update':
                if (window.gpioVisualizer) {
                    window.gpioVisualizer.updatePinState(
                        message.pin, 
                        message.state, 
                        message.mode
                    );
                }
                break;
                
            case 'pwm_state_update':
                if (window.gpioVisualizer) {
                    window.gpioVisualizer.updatePWMState(
                        message.pin, 
                        message.duty_cycle, 
                        message.frequency
                    );
                }
                break;
                
            case 'motor_state_update':
                if (window.motorVisualizer) {
                    window.motorVisualizer.updateMotor(
                        message.name,
                        message.speed,
                        message.direction
                    );
                }
                break;
                
            case 'sensor_data_update':
                if (window.sensorVisualizer) {
                    window.sensorVisualizer.updateSensorValue(
                        message.sensor,
                        message.value,
                        message.unit
                    );
                }
                break;
                
            case 'emu_event':
                handleEmuEvent(message.event);
                break;
                
            case 'pwm_control_response':
                addMessage(`✅ PWM управление применено для пина ${message.pin}`);
                break;
                
            default:
                console.log('Неизвестный тип сообщения:', message);
        }
    }
    
    // Обработчик событий эмуляции
    function handleEmuEvent(event) {
        switch (event.type) {
            case 'pwm_event':
                handlePWMEvent(event);
                break;
            case 'spi_event':
                handleSPIEvent(event);
                break;
            case 'i2c_event':
                handleI2CEvent(event);
                break;
            default:
                console.log('Unknown emulation event:', event);
        }
    }
    
    // Обработчик PWM событий
    function handlePWMEvent(event) {
        if (!window.pwmVisualizer) {
            window.pwmVisualizer = new PWMVisualizer('pwm-visualization');
        }
        
        switch (event.event) {
            case 'init':
                window.pwmVisualizer.addPWM(event.pin, event.frequency);
                addMessage(`📊 PWM инициализирован на пине ${event.pin}, частота ${event.frequency}Hz`);
                break;
            case 'start':
                window.pwmVisualizer.updatePWM(event.pin, event.duty_cycle, event.frequency);
                addMessage(`🚀 PWM запущен на пине ${event.pin}, скважность ${event.duty_cycle}%`);
                break;
            case 'duty_change':
                window.pwmVisualizer.updatePWMDuty(event.pin, event.duty_cycle);
                addMessage(`📈 PWM скважность изменена на пине ${event.pin}: ${event.duty_cycle}%`);
                break;
            case 'freq_change':
                window.pwmVisualizer.updatePWMFrequency(event.pin, event.frequency);
                addMessage(`📶 PWM частота изменена на пине ${event.pin}: ${event.frequency}Hz`);
                break;
            case 'stop':
                window.pwmVisualizer.removePWM(event.pin);
                addMessage(`⏹️ PWM остановлен на пине ${event.pin}`);
                break;
        }
    }
    
    // Обработчик SPI событий
    function handleSPIEvent(event) {
        if (!window.busVisualizer) {
            window.busVisualizer = new BusVisualizer('spi-devices', 'i2c-devices');
        }
        
        switch (event.event) {
            case 'open':
                window.busVisualizer.addSPIDevice(event.bus, event.device, 'SPI Device');
                addMessage(`🔌 SPI устройство открыто: bus ${event.bus}, device ${event.device}`);
                break;
            case 'transfer':
                window.busVisualizer.updateSPIActivity(event.bus, event.device, true);
                addMessage(`📤 SPI передача: bus ${event.bus}, device ${event.device}, данные: [${event.data}]`);
                // Через секунду сбрасываем активность
                setTimeout(() => {
                    window.busVisualizer.updateSPIActivity(event.bus, event.device, false);
                }, 1000);
                break;
        }
    }
    
    // Обработчик I2C событий
    function handleI2CEvent(event) {
        if (!window.busVisualizer) {
            window.busVisualizer = new BusVisualizer('spi-devices', 'i2c-devices');
        }
        
        switch (event.event) {
            case 'read':
                window.busVisualizer.updateI2CActivity(event.address, true);
                window.busVisualizer.updateI2COperation(
                    event.address, 
                    event.event, 
                    event.register, 
                    event.value
                );
                addMessage(`📖 I2C чтение: адрес 0x${event.address.toString(16)}, регистр 0x${event.register.toString(16)}, значение 0x${event.value.toString(16)}`);
                setTimeout(() => {
                    window.busVisualizer.updateI2CActivity(event.address, false);
                }, 1000);
                break;
            case 'write':
                window.busVisualizer.updateI2CActivity(event.address, true);
                window.busVisualizer.updateI2COperation(
                    event.address, 
                    event.event, 
                    event.register, 
                    event.value
                );
                addMessage(`📝 I2C запись: адрес 0x${event.address.toString(16)}, регистр 0x${event.register.toString(16)}, значение 0x${event.value.toString(16)}`);
                setTimeout(() => {
                    window.busVisualizer.updateI2CActivity(event.address, false);
                }, 1000);
                break;
        }
    }
    
    // Функция для обнаружения аппаратных событий
    function detectHardwareEvents(output) {
        if (!window.gpioVisualizer) return;
        
        // Обнаружение GPIO событий
        const gpioOutputMatch = output.match(/GPIO (\d+) output: (True|False)/i);
        const gpioSetupMatch = output.match(/GPIO (\d+) setup as (OUT|IN)/i);
        const pwmMatch = output.match(/PWM.*pin (\d+).*duty cycle (\d+)%/i);
        const motorMatch = output.match(/Motor (\w+).*speed set to (-?\d+)%/i);
        
        if (gpioOutputMatch) {
            const pin = parseInt(gpioOutputMatch[1]);
            const state = gpioOutputMatch[2].toLowerCase() === 'true';
            window.gpioVisualizer.updatePinState(pin, state, 'output');
        }
        
        if (gpioSetupMatch) {
            const pin = parseInt(gpioSetupMatch[1]);
            const mode = gpioSetupMatch[2];
            window.gpioVisualizer.setPinMode(pin, mode.toLowerCase());
        }
        
        if (pwmMatch) {
            const pin = parseInt(pwmMatch[1]);
            const dutyCycle = parseInt(pwmMatch[2]);
            window.gpioVisualizer.updatePWMState(pin, dutyCycle, 100);
        }
        
        if (motorMatch) {
            const name = motorMatch[1];
            const speed = parseInt(motorMatch[2]);
            if (window.motorVisualizer) {
                window.motorVisualizer.updateMotor(name, speed, speed >= 0 ? 1 : -1);
            }
        }
    }
    
    // Функция для добавления сообщений в консоль
    function addMessage(message, type = 'info') {
        const messageElement = document.createElement('div');
        messageElement.className = 'console-' + type;
        messageElement.textContent = message;
        outputConsole.appendChild(messageElement);
        outputConsole.scrollTop = outputConsole.scrollHeight;
        console.log('Console:', message);
    }
    
    // Функция обновления статуса подключения
    function updateStatus(text, className) {
        statusElement.textContent = text;
        statusElement.className = className;
        
        if (className === 'connected') {
            connectionStartTime = new Date();
            startConnectionTimer();
        } else {
            stopConnectionTimer();
        }
    }
    
    // Таймер подключения
    function startConnectionTimer() {
        stopConnectionTimer();
        connectionTimer = setInterval(() => {
            const now = new Date();
            const diff = now - connectionStartTime;
            const hours = Math.floor(diff / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            
            connectionTimeElement.textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    function stopConnectionTimer() {
        if (connectionTimer) {
            clearInterval(connectionTimer);
            connectionTimer = null;
        }
        connectionTimeElement.textContent = '00:00:00';
    }
    
    // Функция подключения WebSocket
    function connectWebSocket() {
        try {
            console.log('Пытаемся подключиться к WebSocket...');
            websocket = new WebSocket(serverUrl);
            
            websocket.onopen = function() {
                console.log('WebSocket подключен');
                updateStatus('✅ Подключено', 'connected');
                addMessage('Подключение к серверу установлено');
            };
            
            websocket.onmessage = function(event) {
                try {
                    console.log('Получено сообщение:', event.data);
                    const message = JSON.parse(event.data);
                    handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Ошибка обработки сообщения:', error);
                    addMessage('Получено: ' + event.data);
                }
            };
            
            websocket.onclose = function() {
                console.log('WebSocket отключен');
                updateStatus('❌ Не подключено', 'disconnected');
                addMessage('Соединение с сервером потеряно');
                // Пытаемся переподключиться через 3 секунды
                setTimeout(connectWebSocket, 3000);
            };
            
            websocket.onerror = function(error) {
                console.error('WebSocket ошибка:', error);
                updateStatus('⚠️ Ошибка подключения', 'disconnected');
            };
            
        } catch (error) {
            console.error('Ошибка создания WebSocket:', error);
            updateStatus('❌ Ошибка подключения', 'disconnected');
        }
    }
    
    // Функция выполнения кода
    function executeCode() {
        const code = codeTextarea.value.trim();
        if (!code) {
            addMessage('❌ Ошибка: Пустой код', 'error');
            return;
        }
        
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            addMessage('❌ Ошибка: Нет соединения с сервером', 'error');
            return;
        }
        
        addMessage('Отправка кода на выполнение...');
        
        try {
            websocket.send(JSON.stringify({
                type: 'execute',
                code: code
            }));
        } catch (error) {
            addMessage('❌ Ошибка отправки: ' + error, 'error');
        }
    }
    
    // Функция остановки выполнения
    function stopExecution() {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'stop'
            }));
            addMessage('⏹️ Запрос на остановку отправлен');
        }
    }
    
    // Функция очистки вывода
    function clearOutput() {
        outputConsole.innerHTML = '';
        addMessage('Консоль очищена');
    }
    
    // Функция сохранения кода
    function saveCode() {
        const code = codeTextarea.value;
        localStorage.setItem('saved_code', code);
        addMessage('💾 Код сохранен в локальное хранилище');
    }
    
    // Функция загрузки кода
    function loadCode() {
        const savedCode = localStorage.getItem('saved_code');
        if (savedCode) {
            codeTextarea.value = savedCode;
            addMessage('📂 Код загружен из локального хранилище');
        } else {
            addMessage('❌ Нет сохраненного кода', 'error');
        }
    }
    
    // Функция переключения темы
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        themeToggle.textContent = newTheme === 'light' ? '🌙 Тёмная' : '☀️ Светлая';
        addMessage(`Тема изменена на ${newTheme === 'light' ? 'светлую' : 'тёмную'}`);
    }
    
    // Функция переключения вкладок
    function switchTab(tabName) {
        // Деактивируем все вкладки
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Активируем выбранную вкладку
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Инициализируем PWM визуализатор при переключении на вкладку SPI/I2C
        if (tabName === 'spi-i2c' && !window.pwmVisualizer) {
            window.pwmVisualizer = new PWMVisualizer('pwm-visualization');
        }
    }
    
    // Назначаем обработчики событий
    runButton.addEventListener('click', executeCode);
    stopButton.addEventListener('click', stopExecution);
    clearButton.addEventListener('click', clearOutput);
    saveButton.addEventListener('click', saveCode);
    loadButton.addEventListener('click', loadCode);
    themeToggle.addEventListener('click', toggleTheme);
    helpBtn.addEventListener('click', () => modal.style.display = 'block');
    closeModal.addEventListener('click', () => modal.style.display = 'none');
    
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Запускаем подключение
    connectWebSocket();
    
    // Добавляем тестовое сообщение
    addMessage('Эмулятор Raspberry Pi готов к работе');
    addMessage('Введите код Python и нажмите "Выполнить"');
    
    // Загружаем сохраненный код, если есть
    const savedCode = localStorage.getItem('saved_code');
    if (savedCode) {
        codeTextarea.value = savedCode;
    }
});