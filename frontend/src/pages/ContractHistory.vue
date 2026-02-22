<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useContractStore } from '../stores/contractStore'

const route = useRoute()
const store = useContractStore()
const contractId = computed(() => String(route.params.id || ''))

onMounted(async () => {
  if (contractId.value) {
    await store.loadLogs(contractId.value)
    await store.loadAiInteractions(contractId.value)
  }
})
</script>

<template>
  <section class="card stack">
    <h2>Contract History</h2>
    <h3>Mutation Logs</h3>
    <pre>{{ JSON.stringify(store.logs, null, 2) }}</pre>
    <h3>AI Interactions</h3>
    <pre>{{ JSON.stringify(store.aiInteractions, null, 2) }}</pre>
  </section>
</template>
