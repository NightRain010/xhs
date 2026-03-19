<template>
  <div class="input-area">
    <div class="input-wrapper">
      <textarea
        v-model="text"
        @keydown.enter.exact.prevent="send"
        placeholder="输入你的问题，例如：今天的热点是什么？"
        rows="1"
        :disabled="loading"
      ></textarea>
      <button class="send-btn" @click="send" :disabled="loading || !text.trim()">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['send'])

const text = ref('')

function send() {
  if (!text.value.trim() || props.loading) return
  emit('send', text.value.trim())
  text.value = ''
}
</script>
