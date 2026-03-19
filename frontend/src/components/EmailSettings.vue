<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="close">
      <div class="modal">
        <div class="modal-header">
          <h3>📧 邮件定时发送</h3>
          <button class="modal-close" @click="close">&times;</button>
        </div>
        <div class="modal-body">
          <!-- Schedule List -->
          <div class="schedule-list">
            <div v-if="schedules.length === 0" class="empty-hint">暂无定时任务，请在下方添加</div>
            <div v-for="s in schedules" :key="s.id" class="schedule-item">
              <div class="schedule-info">
                <div class="email">{{ s.recipient_email }}</div>
                <div class="schedule-detail">
                  <span>{{ formatDow(s.cron_day_of_week) }} {{ pad(s.cron_hour) }}:{{ pad(s.cron_minute) }}</span>
                  <span :style="{ color: s.enabled ? '#00b894' : '#e17055' }">{{ s.enabled ? '已启用' : '已暂停' }}</span>
                  <span>{{ s.last_sent_at ? '上次: ' + formatTime(s.last_sent_at) : '尚未发送' }}</span>
                  <span v-if="s.last_send_status" :class="['status-badge', s.last_send_status]">{{ statusText(s.last_send_status) }}</span>
                </div>
              </div>
              <div class="schedule-actions">
                <button class="btn-sm btn-test" @click="testSchedule(s.id)">测试</button>
                <button class="btn-sm btn-edit" @click="editSchedule(s)">编辑</button>
                <button v-if="s.enabled" class="btn-sm btn-toggle-off" @click="toggleSchedule(s.id, false)">暂停</button>
                <button v-else class="btn-sm btn-toggle-on" @click="toggleSchedule(s.id, true)">启用</button>
                <button class="btn-sm btn-del" @click="deleteSchedule(s.id)">删除</button>
              </div>
            </div>
          </div>

          <!-- Form -->
          <div class="form-title">{{ editingId ? '编辑任务 #' + editingId : '添加新任务' }}</div>

          <div class="form-group">
            <label>收件人邮箱</label>
            <input v-model="form.email" type="email" placeholder="example@qq.com" />
          </div>

          <div class="form-group">
            <label>邮件主题（{date} 会替换为当天日期）</label>
            <input v-model="form.subject" type="text" placeholder="小红书热点日报 - {date}" />
          </div>

          <div class="form-group">
            <label>发送时间</label>
            <div class="time-inputs">
              <input v-model.number="form.hour" type="number" min="0" max="23" />
              <span>时</span>
              <input v-model.number="form.minute" type="number" min="0" max="59" />
              <span>分</span>
            </div>
          </div>

          <div class="form-group">
            <label>发送日期（不选则每天发送）</label>
            <div class="day-picker">
              <label v-for="d in dayOptions" :key="d.value" :class="{ checked: form.days.includes(d.value) }">
                <input type="checkbox" :value="d.value" v-model="form.days" />
                {{ d.label }}
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>Agent 提示词（让 AI 为你生成什么内容）</label>
            <textarea v-model="form.prompt" rows="2" placeholder="获取小红书今日热搜榜单，并做简要分析"></textarea>
          </div>

          <div class="form-actions">
            <button class="btn-primary" @click="submitForm">{{ editingId ? '保存修改' : '添加定时任务' }}</button>
            <button v-if="editingId" class="btn-secondary" @click="cancelEdit">取消编辑</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const dayOptions = [
  { value: 'mon', label: '一' },
  { value: 'tue', label: '二' },
  { value: 'wed', label: '三' },
  { value: 'thu', label: '四' },
  { value: 'fri', label: '五' },
  { value: 'sat', label: '六' },
  { value: 'sun', label: '日' },
]

const schedules = ref([])
const editingId = ref(null)
const form = ref(defaultForm())

function defaultForm() {
  return {
    email: '',
    subject: '小红书热点日报 - {date}',
    hour: 9,
    minute: 0,
    days: [],
    prompt: '获取小红书今日热搜榜单，并做简要分析',
  }
}

function pad(n) { return String(n).padStart(2, '0') }

function formatTime(t) {
  if (!t) return ''
  return t.slice(0, 16).replace('T', ' ')
}

function formatDow(dow) {
  if (!dow || dow === '*') return '每天'
  const map = { mon: '周一', tue: '周二', wed: '周三', thu: '周四', fri: '周五', sat: '周六', sun: '周日' }
  return dow.split(',').map(d => map[d] || d).join(' ')
}

function statusText(s) {
  return { success: '发送成功', failed: '发送失败', empty: '内容为空' }[s] || s
}

watch(() => props.visible, (v) => {
  if (v) { loadSchedules(); cancelEdit() }
})

async function loadSchedules() {
  try {
    const res = await axios.get('/api/email-schedules')
    schedules.value = res.data
  } catch (e) { console.error(e) }
}

function editSchedule(s) {
  editingId.value = s.id
  form.value = {
    email: s.recipient_email,
    subject: s.email_subject || '小红书热点日报 - {date}',
    hour: s.cron_hour,
    minute: s.cron_minute,
    days: (!s.cron_day_of_week || s.cron_day_of_week === '*') ? [] : s.cron_day_of_week.split(','),
    prompt: s.prompt,
  }
}

function cancelEdit() {
  editingId.value = null
  form.value = defaultForm()
}

async function submitForm() {
  const f = form.value
  if (!f.email) { alert('请输入收件人邮箱'); return }
  if (f.hour < 0 || f.hour > 23) { alert('小时应在 0-23 之间'); return }
  if (f.minute < 0 || f.minute > 59) { alert('分钟应在 0-59 之间'); return }

  const body = {
    recipient_email: f.email,
    email_subject: f.subject || '小红书热点日报 - {date}',
    cron_hour: f.hour,
    cron_minute: f.minute,
    cron_day_of_week: f.days.length ? f.days.join(',') : '*',
    prompt: f.prompt || '获取小红书今日热搜榜单，并做简要分析',
  }

  try {
    if (editingId.value) {
      await axios.put(`/api/email-schedules/${editingId.value}`, body)
    } else {
      await axios.post('/api/email-schedules', body)
    }
    cancelEdit()
    loadSchedules()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    alert('操作失败: ' + msg)
  }
}

async function toggleSchedule(id, enabled) {
  try {
    await axios.put(`/api/email-schedules/${id}`, { enabled })
    loadSchedules()
  } catch (e) { console.error(e) }
}

async function testSchedule(id) {
  if (!confirm('将立即执行一次 Agent 查询并发送测试邮件，确认？')) return
  try {
    const res = await axios.post(`/api/email-schedules/${id}/test`)
    alert(res.data.message || '测试完成')
    loadSchedules()
  } catch (e) {
    alert('测试失败，请检查后端日志')
  }
}

async function deleteSchedule(id) {
  if (!confirm('确认删除此定时任务？')) return
  try {
    await axios.delete(`/api/email-schedules/${id}`)
    if (editingId.value === id) cancelEdit()
    loadSchedules()
  } catch (e) { console.error(e) }
}

function close() { emit('close') }
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 560px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  animation: fadeIn .25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--accent), #ff6b7a);
  border-radius: 16px 16px 0 0;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: #fff;
}

.modal-close {
  background: rgba(255,255,255,0.2);
  border: none;
  font-size: 22px;
  cursor: pointer;
  color: #fff;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background .15s;
}

.modal-close:hover { background: rgba(255,255,255,0.35); }

.modal-body { padding: 20px 24px; }

/* Schedule List */
.schedule-list { margin-bottom: 16px; }

.schedule-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 8px;
  transition: all .15s;
  background: var(--bg-tertiary);
}

.schedule-item:hover {
  border-color: var(--accent);
  box-shadow: 0 2px 12px rgba(255,71,87,0.1);
}

.schedule-info { flex: 1; min-width: 0; }

.schedule-info .email {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
}

.schedule-detail {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.schedule-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  margin-left: 12px;
}

.btn-sm {
  background: none;
  border: 1px solid var(--border);
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all .15s;
}

.btn-test {
  color: var(--accent);
  border-color: var(--accent);
}
.btn-test:hover { background: rgba(255,71,87,0.1); }

.btn-edit {
  color: var(--text-secondary);
  border-color: var(--border);
}
.btn-edit:hover { background: var(--bg-hover); color: var(--text-primary); }

.btn-toggle-off {
  color: #e17055;
  border-color: #e17055;
}
.btn-toggle-off:hover { background: rgba(225,112,85,0.1); }

.btn-toggle-on {
  color: #00b894;
  border-color: #00b894;
}
.btn-toggle-on:hover { background: rgba(0,184,148,0.1); }

.btn-del {
  color: var(--text-secondary);
  border-color: var(--border);
}
.btn-del:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(255,71,87,0.1);
}

.status-badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.success { background: rgba(0,184,148,0.15); color: #00b894; }
.status-badge.failed { background: rgba(255,71,87,0.15); color: var(--accent); }
.status-badge.empty { background: rgba(225,112,85,0.15); color: #e17055; }

.empty-hint {
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 20px 0;
}

/* Form */
.form-title {
  font-size: 14px;
  font-weight: 600;
  margin: 20px 0 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  color: var(--accent);
}

.form-group { margin-bottom: 14px; }

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.form-group input, .form-group textarea {
  width: 100%;
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color .2s;
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.form-group input::placeholder, .form-group textarea::placeholder {
  color: var(--text-secondary);
}

.form-group input:focus, .form-group textarea:focus {
  border-color: var(--accent);
}

.time-inputs { display: flex; gap: 8px; align-items: center; }
.time-inputs input { width: 80px; text-align: center; }
.time-inputs span { font-size: 14px; color: var(--text-secondary); }

.day-picker { display: flex; gap: 6px; flex-wrap: wrap; }

.day-picker label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: 2px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all .15s;
  user-select: none;
  color: var(--text-secondary);
}

.day-picker label:hover {
  border-color: var(--text-secondary);
  color: var(--text-primary);
}

.day-picker label.checked {
  border-color: var(--accent);
  background: rgba(255,71,87,0.1);
  color: var(--accent);
  font-weight: 500;
}

.day-picker input { display: none; }

.form-actions { display: flex; gap: 8px; margin-top: 4px; }

.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background .2s;
}

.btn-primary:hover { background: var(--accent-hover); }

.btn-secondary {
  background: none;
  border: 1px solid var(--border);
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all .15s;
}

.btn-secondary:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
</style>
