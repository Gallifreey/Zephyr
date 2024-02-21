<!-- eslint-disable vue/multi-word-component-names -->
<template>
    <div class="container">
        <span v-if="!flag">{{ currentIndex!==(Object.keys(labels).length)?`现在，请开始选择${Object.keys(labels)[currentIndex]}点位`:`标定完毕` }}</span>
        <img v-if="flag" id="video2" />
        <div class="labeling-canvas"
        style="display: flex;">
            <canvas v-if="!flag" id="zoom-canvas" :width="zoom_size[0]" :height="zoom_size[1]"></canvas>
            <canvas v-if="!flag" id="video2-canvas" width="900px" height="540px"></canvas>
        </div>
        <div style="display: flex;margin-top: 10px;">
            <a-button block v-if="currentIndex === Object.keys(labels).length" style="margin-right: 10px;" @click="submit()">发送</a-button>
            <a-button block @click="start()">{{ flag?'开始标定':'重新标定' }}</a-button>
        </div>
    </div>
</template>

<script>
import { RadarWebSocketSerive } from '@/utils/socket'
import { LabelDict } from '@/utils/util'

export default {
    props: {
        open: {
            type: Boolean,
            default: false
        }
    },
    data(){
        return {
            calibrateWS: undefined,
            calibrationDataWS: undefined,
            refreshTimer: undefined,
            background: "http://localhost:8080/demo.png",
            flag: true,
            dpr: 0.9,
            currentIndex: 0,
            labels: LabelDict,
            ctx: undefined,
            zoom_size: [300, 300],
            zoom_scale: 50,
            labellingPoints: []
        }
    },
    mounted(){
        this.calibrateWS = new RadarWebSocketSerive(1004)
        this.calibrateWS.onMessage = this.onCalibrateWSMessage
        this.calibrateWS.start()
        this.calibrationDataWS = new RadarWebSocketSerive(1005)
        this.calibrationDataWS.start()
    },
    unmounted(){
        this.calibrateWS.stop()
        this.calibrationDataWS.stop()
    },
    computed(flag) {
        if(!this.flag) this.refreshTimer.clear()
    },
    methods: {
        submit(){
            const canvas = document.getElementById("video2-canvas")
            // 提交四点，标定完毕
            this.calibrationDataWS.send(JSON.stringify({
                labels: this.labels,
                size: [canvas.width, canvas.height]
            }))
        },
        onCalibrateWSMessage(evt){
            if(this.flag){
                var data = JSON.parse(evt.data)
                document.getElementById('video2').src = data['img']
                this.background = data['img']
            }
        },
        init(){

        },
        render(){
            const canvas = document.getElementById('video2-canvas')
            const zoom = document.getElementById('zoom-canvas')
            const ctx = canvas.getContext("2d")
            const zoomCtx = zoom.getContext("2d")
            var image = new Image()
            var zoomView = new Image()
            const mouse = this.getMouse(canvas, zoomCtx, zoomView)
            image.src = this.background
            image.onload = () => {
                ctx.drawImage(image, 0, 0, image.width, image.height, 0, 0, canvas.width, canvas.height)
            }
            this.refreshTimer = setInterval(() => {
                zoomView.src = canvas.toDataURL("image/jpg")
            }, 500)
            ctx.save()
            this.ctx = ctx
            canvas.addEventListener('mousedown', (e) => {
                if(this.currentIndex === Object.keys(this.labels).length) return
                if(e.ctrlKey) this.drawPoint(ctx, mouse.x, mouse.y)
                if(e.altKey){
                    if(this.isClickLabel([mouse.x, mouse.y])) console.log(ctx == this.ctx);
                }
            })
        },
        start(){
            this.flag = !this.flag
            if(!this.flag){
                // delay until dom rendered
                setTimeout(() => {
                    this.render()
                }, 1)
            }else{
                clearInterval(this.refreshTimer)
                this.currentIndex = 0
            }

        },
        getMouse(element, zoomCtx, oriView){
            let mouse = { x: 0, y: 0 } // 存储鼠标位置信息
            element.addEventListener('mousemove', e => {
                let x = e.clientX
                let y = e.clientY
                var rect = element.getBoundingClientRect()
                // 计算鼠标在canvas画布中的相对位置
                mouse.x = x - rect.left
                mouse.y = y - rect.top
                // 放大
                if(oriView.src){
                    const w = this.zoom_size[0]
                    const h = this.zoom_size[1]
                    zoomCtx.drawImage(oriView, Math.max(0, mouse.x - this.zoom_scale),
                    Math.max(0, mouse.y - this.zoom_scale), 2 * this.zoom_scale, 2 * this.zoom_scale, 0, 0, w, h)
                    // 画线
                    zoomCtx.strokeStyle = 'green'
                    zoomCtx.beginPath()
                    zoomCtx.moveTo(0, h / 2)
                    zoomCtx.lineTo(w, h / 2)
                    zoomCtx.stroke()
                    zoomCtx.closePath()
                    zoomCtx.beginPath()
                    zoomCtx.moveTo(w / 2, 0)
                    zoomCtx.lineTo(w / 2, h)
                    zoomCtx.stroke()
                    zoomCtx.closePath()
                }

            })
            return mouse
        },
        drawPoint(ctx, x, y){
            this.labels[Object.keys(this.labels)[this.currentIndex]] = [x, y]
            ctx.beginPath()
            ctx.arc(x, y, 5, 0, 2 * Math.PI)
            ctx.fillStyle = 'red'
            ctx.fill()
            ctx.closePath()
            // 连线
            if(this.currentIndex !== 0) this.drawLine(ctx, this.labels[Object.keys(this.labels)[this.currentIndex - 1]], this.labels[Object.keys(this.labels)[this.currentIndex]])
            if(this.currentIndex === Object.keys(this.labels).length - 1) this.drawLine(ctx, this.labels[Object.keys(this.labels)[0]], this.labels[Object.keys(this.labels)[this.currentIndex]])
            this.currentIndex++
        },
        drawLine(ctx, s, e){
            ctx.beginPath()
            ctx.moveTo(...s)
            ctx.lineTo(...e)
            ctx.strokeStyle = 'green'
            ctx.stroke()
            ctx.closePath()
        },
        drawZomm(ctx, canvas){
            ctx, canvas
        },
        isClickLabel(point){
            for(const label of this.labels){
                if(this.isInTheCircle(point, label.point, 10)){
                    label.point = [0, 0]
                    this.ctx.restore()
                    this.currentIndex--
                    return true
                }
            }
            return false
        },
        isInTheCircle(target, center, radius){
            const x = target[0]
            const y = target[1]
            const cx = center[0]
            const cy = center[1]
            return radius >= Math.sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy))
        }
    }
}
</script>

<style lang="scss" scoped>
.container{
    position: relative;
    height: 500;
    width: 600;
    img{
        height: 500px;
    }
    span{
        font-size: 25px;
    }
}
</style>