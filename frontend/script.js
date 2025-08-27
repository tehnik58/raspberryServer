document.addEventListener('DOMContentLoaded', function() {
    console.log('Документ загружен, инициализируем приложение...');
    
    // Получаем элементы DOM
    const codeTextarea = document.getElementById('python-code');
    const runButton = document.getElementById('run-btn');
    const stopButton = document.getElementById('stop-btn');
    const clearButton = document.getElementById('clear-btn');
    const outputConsole = document.getElementById('output-console');
    const statusElement = document.getElementById('status');
    
    let websocket = null;
    const serverUrl = 'ws://' + window.location.hostname + ':8000/ws/execute';
    // Обработчик сообщений от сервера
function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'output':
            addMessage(message.content);
            
            // Автоматически обнаруживаем GPIO события
            detectGPIOEvents(message.content);
            break;
            
        case 'error':
            addMessage(`❌ Ошибка: ${message.content}`, 'error');
            break;
            
        case 'execution_started':
            addMessage('🚀 Выполнение началось');
            runButton.disabled = true;
            // Сбрасываем визуализацию при начале выполнения
            if (window.gpioVisualizer) {
                window.gpioVisualizer.resetAllPins();
            }
            break;
            
        case 'execution_completed':
            addMessage('✅ Выполнение завершено');
            runButton.disabled = false;
            break;
            
        default:
            console.log('Неизвестный тип сообщения:', message);
    }
}

// Функция для обнаружения GPIO событий
function detectGPIOEvents(output) {
    if (!window.gpioVisualizer) return;

    const gpioOutputMatch = output.match(/GPIO (\d+) output: (True|False)/i);
    const gpioSetupMatch = output.match(/GPIO (\d+) setup as (OUT|IN)/i);

    if (gpioOutputMatch) {
        const pin = parseInt(gpioOutputMatch[1]);
        const state = gpioOutputMatch[2].toLowerCase() === 'true';
        window.gpioVisualizer.updatePinState(pin, state, 'output');
        
        // Отправляем обновление состояния на сервер
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'gpio_state_update',
                pin: pin,
                state: state,
                mode: 'output'
            }));
        }
    }
    
    if (gpioSetupMatch) {
        const pin = parseInt(gpioSetupMatch[1]);
        const mode = gpioSetupMatch[2];
        window.gpioVisualizer.setPinMode(pin, mode.toLowerCase());
        addMessage(`📌 GPIO ${pin} настроен как ${mode === 'OUT' ? 'выход' : 'вход'}`);
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
    
    // Функция обновления статуса
    function updateStatus(text, className) {
        statusElement.textContent = text;
        statusElement.className = className;
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
                    
                    switch (message.type) {
                        case 'output':
                            addMessage(message.content);
                            break;
                        case 'error':
                            addMessage('❌ Ошибка: ' + message.content, 'error');
                            break;
                        case 'execution_started':
                            addMessage('🚀 Выполнение началось');
                            runButton.disabled = true;
                            break;
                        case 'execution_completed':
                            addMessage('✅ Выполнение завершено');
                            runButton.disabled = false;
                            break;
                        default:
                            addMessage('Неизвестный тип сообщения: ' + message.type);
                    }
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
    
    // Назначаем обработчики событий
    runButton.addEventListener('click', executeCode);
    stopButton.addEventListener('click', stopExecution);
    clearButton.addEventListener('click', clearOutput);
    
    // Тестируем кнопки
    console.log('Кнопки назначены:', {
        run: runButton,
        stop: stopButton,
        clear: clearButton
    });
    
    // Запускаем подключение
    connectWebSocket();
    
    // Добавляем тестовое сообщение
    addMessage('Эмулятор Raspberry Pi готов к работе');
    addMessage('Введите код Python и нажмите "Выполнить"');
});