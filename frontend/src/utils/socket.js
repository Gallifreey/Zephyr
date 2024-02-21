export class RadarWebSocketSerive {
    websocket = undefined
    host = "192.168.2.10"
    port = 1000
    constructor(port) {
        this.port = port
        this.websocket = new WebSocket(`ws://${this.host}:${this.port}/`)
    }
    onMessage(event) {
        event
    }
    start(){
        this.websocket.onmessage = this.onMessage
    }
    stop(){
        this.websocket.close()
    }
    send(data) {
        this.websocket.send(data)
    }
}