<template>
  <div class="messages-container" ref="container">
    <!-- Welcome -->
    <div v-if="messages.length === 0 && !loading" class="welcome">
      <div class="welcome-icon">&#128214;</div>
      <h2>你好！我是小红书热点助手</h2>
      <p>你可以问我：</p>
      <div class="suggestions">
        <button
          v-for="s in suggestions"
          :key="s"
          class="suggestion-btn"
          @click="$emit('use-suggestion', s)"
        >{{ s }}</button>
      </div>
    </div>

    <!-- Messages -->
    <div
      v-for="(msg, i) in messages"
      :key="i"
      :class="['message', msg.role]"
    >
      <div class="avatar">{{ msg.role === 'user' ? '&#128100;' : '&#129302;' }}</div>
      <div class="bubble">
        <div v-html="renderMarkdown(msg.content)"></div>
        <span v-if="streaming && i === messages.length - 1 && msg.role === 'assistant'" class="cursor-blink">|</span>
      </div>
    </div>

    <!-- Loading (before stream starts) -->
    <div v-if="loading && !streaming && messages[messages.length - 1]?.role === 'user'" class="message assistant">
      <div class="avatar">&#129302;</div>
      <div class="bubble loading-bubble">
        <div class="dot-pulse">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div ref="anchor"></div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  streaming: { type: Boolean, default: false },
})

defineEmits(['use-suggestion'])

const anchor = ref(null)

const suggestions = [
  '今天小红书有什么热点？',
  '最近什么话题最火？',
  '帮我看看热搜榜单',
]

function renderMarkdown(content) {
  if (!content) return ''
  return md.render(content)
}

watch(
  () => {
    const last = props.messages[props.messages.length - 1]
    return [props.messages.length, props.loading, props.streaming, last?.content?.length || 0]
  },
  async () => {
    await nextTick()
    anchor.value?.scrollIntoView({ behavior: 'smooth' })
  },
)
</script>
