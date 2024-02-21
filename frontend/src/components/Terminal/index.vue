<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="container">
    <Codemirror 
     class="cm" 
     v-model="code" 
     KeepCursorInEnd 
     style="height: 90%;"
     :extensions="extensions"
    />
    <div id="command">
      <a-space-compact block>
        <a-input 
        placeholder="指令以'/'开始，以助记符和指令作为标记。"
        >
        </a-input>
        <a-button type="primary">
          发送
        </a-button>
        <a-button danger type="primary">
          清除
        </a-button>
        <a-button type="primary">
          查看指令映射表
        </a-button>
        <a-button type="primary">
          查看指令协议
        </a-button>
      </a-space-compact>
    </div>
  </div>
</template>

<script>
import { Codemirror } from 'vue-codemirror'
import { EditorState } from "@codemirror/state"
import { EditorView } from "codemirror"
import { RadarWebSocketSerive } from '@/utils/socket'

export default {
  data(){
    return {
      code: "",
      command: '',
      tipsVisible: false,
      seqFormatVisible: false,
      extensions: [
        EditorView.editable.of(false),
        EditorState.readOnly.of(true)
      ]
    }
  },
  components: {
    Codemirror
  },
  mounted(){
    let commandWS = new RadarWebSocketSerive(1003)
    commandWS.onMessage = this.onCommandWSMessgae
    commandWS.start()
  },
  methods: {
    onCommandWSMessgae (evt) {
      this.code += (`${evt.data}\n`)
      if (this.code.length > 20000) {
        this.code = this.code.substring(10000, this.code.length)
      }
    },
    onCommandWSSend () {
      this.commandWS.send(this.command)
    },
  }
}
</script>

<style lang="scss" scoped>
.container{
  height: 35vh;
  margin: 5px;
  width: calc(100% - 5px);
}
</style>