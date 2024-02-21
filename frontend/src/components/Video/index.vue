<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="container" @mouseenter="hover=true" @mouseleave="hover=false">
    <div class="video-monitor">
      <img id="video" />
      <div v-if="isRecording" id="record-mask">
        <div v-if="recordMsgShow">
          {{ recordMsg }}
        </div>
      </div>
      <div v-if="debug" id="info-bar">
        <a-space>
          <span>
            {{ debugMsg['cam_fps'] }} fps(CAM)
          </span>
          <span>
            {{ debugMsg['freq'] }} hz
          </span>
          <span>
            {{ debugMsg['lda_fps'] }} fps(LDA)
          </span>
        </a-space>
      </div>
      <transition name="fade">
        <div id="bar" v-if="hover">
          <a-row>
            <a-col :span="8">
              <a-space>
                <a-tooltip title="停止录制" @click="stopRecord()">
                  <a-button size="large">
                    <template #icon>
                      <StopFilled />
                    </template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="回放">
                  <a-button size="large">
                    <template #icon>
                      <PlayCircleFilled />
                    </template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="开始录制">
                  <a-button size="large" @click="startRecord()">
                    <template #icon>
                      <CheckCircleFilled />
                    </template>
                  </a-button>
                </a-tooltip>
              </a-space>
            </a-col>
            <a-col :span="16">
              <div style="position: relative;color: white;display: flex;align-items: center;">
                <span>0:0:0</span>
                <a-slider style="width: 500px;" v-model:value="sliderValue" :min="0" :max="100" />
                <span>-:-:-</span>
              </div>
            </a-col>
          </a-row>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
import { StopFilled, PlayCircleFilled, CheckCircleFilled } from '@ant-design/icons-vue'
import { RadarWebSocketSerive } from '@/utils/socket'

export default {
  data(){
    return {
      hover: false,
      isRecording: false,
      debug: false,
      recordMsg: '◉REC',
      recordMsgShow: true,
      recordPointer: null,
      sliderValue: 50,
      debugMsg: {
        cam_fps: 0,
        freq: 10,
        lda_fps: 0
      }
    }
  },
  components: {
    StopFilled,
    PlayCircleFilled,
    CheckCircleFilled
  },
  mounted(){
    let videoWS = new RadarWebSocketSerive(1000)
    videoWS.onMessage = this.onVideoWSMessage
    videoWS.start()
  },
  methods: {
    onVideoWSMessage (evt) {
      var data = JSON.parse(evt.data)
      document.getElementById('video').src = data['img']
    },
    startRecord(){
      if(this.isRecording) return
      this.isRecording = true
      this.recordPointer = setInterval(()=>{
        this.recordMsgShow = !this.recordMsgShow
      }, 500)
    },
    stopRecord(){
      if(!this.isRecording) return
      this.isRecording = false
      clearInterval(this.recordPointer)
    }
  }
}
</script>

<style lang="scss" scoped>
.container{
    height: 60vh;
    margin: 5px;
    width: calc(100% - 5px);
    cursor: pointer;
    .video-monitor{
      height: 100%;
      width: 100%;
      position: relative;
      #video{
        height: 100%;
        width: 100%;
      }
      #bar{
        position: absolute;
        bottom: 0;
        height: 50px;
        width: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        padding: 5px;
        padding-left: 10px;
        padding-right: 10px;
        #slider-bar{
          display: flex;
          align-items: center;
        }
      }
      #record-mask{
        position: absolute;
        top: 0;
        right: 0;
        height: 30px;
        background: transparent;
        color: red;
        font-size: 24px;
      }
      #info-bar{
        position: absolute;
        top: 0;
        left: 0;
        height: 30px;
        display: flex;
        align-items: center;
        color: green;
        span{
          font-size: 20px;
        }
      }
    }
}
.fade-enter-active, .fade-leave-active {
  transition: opacity .3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

</style>