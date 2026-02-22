<script setup lang="ts">
import { ref } from 'vue'
import { useContractStore } from '../stores/contractStore'

const props = defineProps<{ contractId: string }>()
const store = useContractStore()
const message = ref('')

const send = async () => {
  if (!message.value.trim()) return
  await store.sendChat(props.contractId, message.value)
  message.value = ''
}
</script>

<template>
  <div class="card stack">
    <h3>AI Assistant</h3>
    <p>Structured-only action pipeline (no raw text edits).</p>
    <textarea v-model="message" rows="3" placeholder="Example: set arras amount to 6000" />
    <button class="primary" @click="send">Apply AI Suggestion</button>
    <p v-if="store.error" class="error">{{ store.error }}</p>
  </div>
</template>
