<script setup lang="ts">
defineProps<{ logs: any[]; aiInteractions: any[] }>()
</script>

<template>
  <div class="card stack">
    <h3>Change Log</h3>
    <p>Every mutation and AI attempt is traceable.</p>
    <pre>{{ JSON.stringify(logs, null, 2) }}</pre>
    <h4>AI Interactions</h4>
    <pre>{{ JSON.stringify(aiInteractions, null, 2) }}</pre>
  </div>
</template>
