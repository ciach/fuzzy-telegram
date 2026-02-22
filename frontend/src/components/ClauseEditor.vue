<script setup lang="ts">
const props = defineProps<{ clauses: Record<string, string> }>()
const emit = defineEmits<{ (e: 'save-clause', payload: { path: string; value: string }): void }>()
</script>

<template>
  <div class="card stack">
    <h3>Legal Clauses</h3>
    <p class="hint">
      Use placeholders for automatic propagation:
      <code v-pre>{{buyers_names}}</code>,
      <code v-pre>{{sellers_names}}</code>,
      <code v-pre>{{total_price_eur}}</code>,
      <code v-pre>{{arras_amount_eur}}</code>,
      <code v-pre>{{remaining_amount_eur}}</code>,
      <code v-pre>{{deadline_date}}</code>.
    </p>
    <label v-for="(value, id) in props.clauses" :key="id">
      {{ id }}
      <textarea
        :value="value"
        rows="5"
        :placeholder="`Example for ${id}: The buyer delivers the arras amount by bank transfer on signing date...`"
        @change="emit('save-clause', { path: `clauses.${id}`, value: ($event.target as HTMLTextAreaElement).value })"
      />
    </label>
  </div>
</template>
