<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="container">
    <canvas id="minimap" height="750px" width="350px"></canvas>
  </div>
</template>

<script>
import { RadarWebSocketSerive } from '@/utils/socket'
import { LabelArray, rw, rh } from '@/utils/util'
import { toRaw } from 'vue'

export default {
  data(){
    return {
      elements: undefined,
      labels: LabelArray,
      rw: rw,
      rh: rh,
      realtimeMsg: []
    }
  },
  mounted(){
    let preInitWS = new RadarWebSocketSerive(1001)
    let reprojectWS = new RadarWebSocketSerive(1002)
    preInitWS.onMessage = this.onPreInitWSMessage
    reprojectWS.onMessage = this.onReprojectWSMessage
    preInitWS.start()
    reprojectWS.start()
  },
  methods: {
    onPreInitWSMessage (evt) {
      this.elements = JSON.parse(evt.data)
      this.renderMap()
    },
    onReprojectWSMessage (evt) {
      this.realtimeMsg = JSON.parse(evt.data)['data']
      this.updateMap()
    },
    renderMap () {
      // render Minimap
      var canvas = document.getElementById('minimap')
      var ctx = canvas.getContext('2d')
      var size = canvas.getBoundingClientRect()
      var height = size.height
      var width = size.width
      let map = new Image()
      map.src = require('@/assets/battlefield.png')
      map.onload = () => {
        ctx.drawImage(map, 0, 0, width, height)
        var ratioW = width / 592
        var ratioH = height / 1107
        var alertPoints = this.elements['alert_region']
        for (const keys in alertPoints) {
          ctx.beginPath()
          for (const point of alertPoints[keys]) {
            ctx.lineTo(point[0] * ratioW, point[1] * ratioH)
          }
          ctx.closePath()
          ctx.lineWidth = 2
          ctx.strokeStyle = 'red'
          ctx.fillStyle = 'rgba(225,225,225,0.5)'
          ctx.fill()
          ctx.stroke()
        }
        for (const keys in alertPoints) {
          ctx.beginPath()
          for (const point of alertPoints[keys]) {
            ctx.lineTo(width - point[0] * ratioW, height - point[1] * ratioH)
          }
          ctx.closePath()
          ctx.lineWidth = 2
          ctx.strokeStyle = 'blue'
          ctx.fillStyle = 'rgba(225,225,225,0.5)'
          ctx.fill()
          ctx.stroke()
        }
        this.savedMap = ctx.getImageData(0, 0, width, height)
      }
    },
    updateMap () {
      var canvas = document.getElementById('minimap')
      var ctx = canvas.getContext('2d')
      var size = canvas.getBoundingClientRect()
      var height = size.height
      var width = size.width
      var ratioW = width / 592
      var ratioH = height / 1107
      // 画点
      this.drawRobot(ctx, this.realtimeMsg, ratioW, ratioH)
    },
    drawRobot(ctx, robots, ratioW, ratioH){
      for(const robot of Object.entries(robots)){
        const name = robot[0]
        const x = robot[1][0]
        const y = robot[1][1]
        const label = this.labels[name]
        const color = label[0] === 'R' ? 'red' : 'blue'
        ctx.beginPath()
        ctx.arc(x * this.rw * ratioW, y * this.rh * ratioH, 5, 0, 2 * Math.PI)
        ctx.fillStyle = color
        ctx.fill()
        ctx.closePath()
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.container{
  height: 60vh;
  margin: 5px;
  width: calc(100% - 5px);
}
</style>