<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useContractStore } from '../stores/contractStore'

const router = useRouter()
const store = useContractStore()

const createContract = async () => {
  const contract = await store.createContract('es', 'Barcelona')
  router.push(`/contracts/${contract.id}`)
}
</script>

<template>
  <section class="card stack">
    <p class="eyebrow">Control Panel</p>
    <h2>Start New Arras Contract</h2>
    <p>Canonical language is Spanish. Catalan and English will derive from validated source content.</p>
    <button class="primary" :disabled="store.loading" @click="createContract">
      {{ store.loading ? 'Creating...' : 'Create Contract Draft' }}
    </button>
    <p v-if="store.error" class="error">{{ store.error }}</p>
  </section>
</template>
