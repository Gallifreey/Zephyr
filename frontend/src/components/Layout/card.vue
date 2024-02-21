<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <div class="container">
    <slot name="cover"></slot>
  </div>
</template>

<script>
export default {

}
</script>

<style lang="scss" scoped>
.container{
  padding-right: 5px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  background: white;
}
</style>
