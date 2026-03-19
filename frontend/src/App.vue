<template>
  <div class="app">
    <Sidebar
      :conversations="conversations"
      :currentConvId="currentConvId"
      :open="sidebarOpen"
      @new-chat="startNewChat"
      @select="selectConversation"
      @delete="deleteConversation"
      @open-email="emailModalOpen = true"
    />

    <EmailSettings
      :visible="emailModalOpen"
      @close="emailModalOpen = false"
    />
    <main class="chat-main">
      <header class="chat-header">
        <button class="toggle-sidebar" @click="sidebarOpen = !sidebarOpen">&#9776;</button>
        <h1>小红书热点 Agent</h1>
        <span class="powered-by">Powered by DeepSeek</span>
      </header>

      <ChatMessages
        :messages="messages"
        :loading="loading"
        :streaming="streaming"
        @use-suggestion="handleSuggestion"
      />

      <ChatInput
        :loading="loading"
        @send="sendMessage"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Sidebar from './components/Sidebar.vue'
import ChatMessages from './components/ChatMessages.vue'
import ChatInput from './components/ChatInput.vue'
import EmailSettings from './components/EmailSettings.vue'

const conversations = ref([])
const currentConvId = ref(null)
const messages = ref([])
const loading = ref(false)
const streaming = ref(false)
const sidebarOpen = ref(true)
const emailModalOpen = ref(false)

onMounted(() => {
  loadConversations()
})

async function loadConversations() {
  try {
    const res = await axios.get('/api/conversations')
    conversations.value = res.data
  } catch (e) {
    console.error(e)
  }
}

async function selectConversation(id) {
  try {
    const res = await axios.get(`/api/conversations/${id}`)
    currentConvId.value = id
    messages.value = res.data.messages || []
  } catch (e) {
    console.error(e)
  }
}

function startNewChat() {
  currentConvId.value = null
  messages.value = []
}

async function deleteConversation(id) {
  try {
    await axios.delete(`/api/conversations/${id}`)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
    }
    loadConversations()
  } catch (e) {
    console.error(e)
  }
}

function handleSuggestion(text) {
  sendMessage(text)
}

async function sendMessage(text) {
  if (!text.trim() || loading.value) return

  messages.value.push({ role: 'user', content: text })
  loading.value = true
  streaming.value = false

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: currentConvId.value,
        message: text,
      }),
    })

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let assistantIdx = -1

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6)
        if (!jsonStr) continue

        try {
          const data = JSON.parse(jsonStr)

          if (data.event === 'start') {
            currentConvId.value = data.conversation_id
            messages.value.push({ role: 'assistant', content: '' })
            assistantIdx = messages.value.length - 1
            streaming.value = true
          } else if (data.event === 'tool_call') {
            if (assistantIdx >= 0) {
              messages.value[assistantIdx].content += `\n\n> 🔧 正在调用工具: ${data.name}...\n\n`
            }
          } else if (data.event === 'delta') {
            if (assistantIdx >= 0) {
              messages.value[assistantIdx].content += data.content
            }
          } else if (data.event === 'done') {
            streaming.value = false
            if (assistantIdx >= 0) {
              messages.value[assistantIdx].content = messages.value[assistantIdx].content
                .replace(/\n\n> 🔧 正在调用工具:.*?\.\.\.\n\n/g, '')
            }
          } else if (data.event === 'error') {
            streaming.value = false
            const errMsg = '抱歉，请求出错了：' + data.message
            if (assistantIdx >= 0) {
              messages.value[assistantIdx].content = errMsg
            } else {
              messages.value.push({ role: 'assistant', content: errMsg })
            }
          }
        } catch {
          // ignore parse errors
        }
      }
    }

    loadConversations()
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，请求出错了：' + e.message,
    })
    streaming.value = false
  } finally {
    loading.value = false
    streaming.value = false
  }
}
</script>
