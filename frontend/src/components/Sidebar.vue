<template>
  <aside :class="['sidebar', open ? 'open' : 'closed']">
    <div class="sidebar-header">
      <h2>&#128269; 对话列表</h2>
      <button class="new-chat-btn" @click="$emit('new-chat')">+ 新对话</button>
    </div>
    <div class="conv-list">
      <div
        v-for="c in conversations"
        :key="c.id"
        :class="['conv-item', { active: c.id === currentConvId }]"
        @click="$emit('select', c.id)"
      >
        <span class="conv-title">{{ c.title }}</span>
        <button class="delete-btn" @click.stop="$emit('delete', c.id)">&times;</button>
      </div>
      <div v-if="conversations.length === 0" class="empty-hint">还没有对话记录</div>
    </div>
    <div class="sidebar-footer">
      <button class="email-settings-btn" @click="$emit('open-email')">📧 邮件定时发送</button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  conversations: { type: Array, default: () => [] },
  currentConvId: { type: Number, default: null },
  open: { type: Boolean, default: true },
})

defineEmits(['new-chat', 'select', 'delete', 'open-email'])
</script>
