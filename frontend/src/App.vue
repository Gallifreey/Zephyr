<template>
  <a-col :gutter="0">
    <a-row :gutter="0">
      <a-col :xs="24" :sm="24" :md="15" :lg="18" :xl="18">
        <card>
          <template #cover>
            <Video />
          </template>
        </card>
      </a-col>
      <a-col :xs="24" :sm="24" :md="9" :lg="6" :xl="6">
        <card>
          <template #cover>
            <Map />
          </template>
        </card>
      </a-col>
    </a-row>
    <a-row>
      <a-col :xs="24" :sm="24" :md="18" :lg="18" :xl="18">
        <card>
          <template #cover>
            <Terminal />
          </template>
        </card>
      </a-col>
    </a-row>
  </a-col>
  <a-float-button-group trigger="click" tooltip="标定">
    <a-float-button tooltip="相机标定">

    </a-float-button>
    <a-float-button tooltip="雷达相机联合标定">
     
    </a-float-button>
    <a-float-button tooltip="相机环境联合标定" @click="calibrate3 = true">
     
    </a-float-button>
  </a-float-button-group>
  <a-float-button-group trigger="click" tooltip="调试" :style="{ right: '94px' }">
    <a-float-button tooltip="性能分析工具">

    </a-float-button>
  </a-float-button-group>
  <a-float-button-group trigger="click" tooltip="插件" :style="{ right: '164px' }">
    <a-float-button tooltip="插件仓库">

    </a-float-button>
  </a-float-button-group>
  <a-modal v-model:open="calibrate3" style="width: 75vw;text-align: center">
    <Calibrate3Modal :open="calibrate3" />
  </a-modal>
</template>

<script>
import Card from './components/Layout/card.vue'
import Video from './components/Video/index.vue'
import Map from './components/Map/index.vue'
import Terminal from './components/Terminal/index.vue'
import Calibrate3Modal from './components/CalibrateView/env.vue'

export default {
  name: 'App',
  components: {
    Card,
    Video,
    Map,
    Terminal,
    Calibrate3Modal
  },
  data(){
    return{
      calibrate3: false
    }
  }
}
</script>

<style>
#app {

}
</style>
