<script setup lang="ts">
defineProps<{ contract: any }>()
</script>

<template>
  <div class="card stack preview">
    <h3>Live Preview (Spanish Canonical)</h3>
    <pre>{{ JSON.stringify(contract.schema, null, 2) }}</pre>
  </div>
</template>
