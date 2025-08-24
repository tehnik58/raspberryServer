class WebSocketClient {
    constructor() {
        this.socket = null;
        this.reconnectInterval = 3000; // 3 seconds
        this.shouldReconnect = true;
        this.messageHandlers = [];
    }

    connect(url) {
        try {
            this.socket = new WebSocket(url);
            
            this.socket.onopen = () => {
                console.log('WebSocket соединение установлено');
                this.updateStatus('✅ Подключено', 'connected');
            };
            
            this.socket.onmessage = (event) => {
                this.handleMessage(event.data);
            };
            
            this.socket.onclose = (event) => {
                console.log('WebSocket соединение закрыто', event.code, event.reason);
                this.updateStatus('❌ Не подключено', 'disconnected');
                
                // Попытка переподключения
                if (this.shouldReconnect) {
                    setTimeout(() => this.connect(url), this.reconnectInterval);
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket ошибка:', error);
                this.updateStatus('⚠️ Ошибка подключения', 'disconnected');
            };
            
        } catch (error) {
            console.error('Ошибка при создании WebSocket:', error);
        }
    }

    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(message);
            return true;
        } else {
            console.warn('WebSocket не готов к отправке сообщений');
            return false;
        }
    }

    disconnect() {
        this.shouldReconnect = false;
        if (this.socket) {
            this.socket.close();
        }
    }

    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Вызываем все зарегистрированные обработчики
            this.messageHandlers.forEach(handler => {
                try {
                    handler(message);
                } catch (error) {
                    console.error('Ошибка в обработчике сообщения:', error);
                }
            });
        } catch (error) {
            console.error('Ошибка при разборе сообщения:', error, data);
        }
    }

    addMessageHandler(handler) {
        this.messageHandlers.push(handler);
    }

    removeMessageHandler(handler) {
        const index = this.messageHandlers.indexOf(handler);
        if (index > -1) {
            this.messageHandlers.splice(index, 1);
        }
    }

    updateStatus(text, className) {
        const statusElement = document.getElementById('status');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.className = className;
        }
    }
}

// Глобальный экземпляр WebSocket клиента
const wsClient = new WebSocketClient();