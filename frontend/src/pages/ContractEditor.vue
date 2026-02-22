<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import ContractFormTabs from '../components/ContractFormTabs.vue'
import ClauseEditor from '../components/ClauseEditor.vue'
import LivePreview from '../components/LivePreview.vue'
import ChatAssistant from '../components/ChatAssistant.vue'
import VoiceIntake from '../components/VoiceIntake.vue'
import ChangeLogPanel from '../components/ChangeLogPanel.vue'
import { useContractStore } from '../stores/contractStore'

const route = useRoute()
const store = useContractStore()
const tab = ref('metadata')

const contractId = computed(() => String(route.params.id || ''))

onMounted(async () => {
  if (contractId.value) {
    await store.loadContract(contractId.value)
    await store.loadLogs(contractId.value)
    await store.loadAiInteractions(contractId.value)
  }
})

watch(contractId, async (id) => {
  if (id) {
    await store.loadContract(id)
    await store.loadLogs(id)
    await store.loadAiInteractions(id)
  }
})

const exportDocx = async () => {
  if (!contractId.value) return
  await store.exportDocument(contractId.value, 'docx')
}

const exportPdf = async () => {
  if (!contractId.value) return
  await store.exportDocument(contractId.value, 'pdf')
}
</script>

<template>
  <section v-if="store.contract" class="editor-grid">
    <div class="stack">
      <div class="card inline-actions">
        <button class="secondary" @click="exportDocx">Export DOCX</button>
        <button class="secondary" @click="exportPdf">Export PDF</button>
      </div>
      <ContractFormTabs v-model="tab" :contract="store.contract" @save-field="store.updateField(contractId, $event)" />
      <ClauseEditor
        v-if="tab === 'legal clauses'"
        :clauses="store.contract.schema.clauses"
        @save-clause="store.updateField(contractId, $event)"
      />
      <ChatAssistant :contract-id="contractId" />
      <VoiceIntake :contract-id="contractId" />
    </div>
    <div class="stack">
      <LivePreview :contract="store.contract" />
      <ChangeLogPanel :logs="store.logs" :ai-interactions="store.aiInteractions" />
    </div>
  </section>
  <p v-else>Loading contract...</p>
</template>
