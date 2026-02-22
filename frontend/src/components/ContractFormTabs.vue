<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

type PartyDraft = {
  full_name: string
  id_number: string
}

type LanguageCode = 'es' | 'ca' | 'en'

const props = defineProps<{ modelValue: string; contract: any }>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'save-field', payload: { path: string; value: unknown }): void
}>()

const tabs = ['metadata', 'parties', 'property', 'financial', 'legal clauses']
const sectionError = ref('')

const sellersDraft = ref<PartyDraft[]>([])
const buyersDraft = ref<PartyDraft[]>([])

const metadataDraft = reactive({
  location: '',
  date: '',
  language: 'es' as LanguageCode
})

const propertyDraft = reactive({
  address: '',
  registry: '',
  cargasText: '',
  ibi: 0
})

const financialDraft = reactive({
  total_price: 0,
  arras_amount: 0,
  deadline: ''
})

const financial = computed(() => props.contract.schema.financial)

const save = (path: string, value: unknown) => emit('save-field', { path, value })

const toPartyDraft = (party: any): PartyDraft => ({
  full_name: party?.full_name ?? '',
  id_number: party?.id_number ?? ''
})

const syncFromContract = () => {
  const schema = props.contract?.schema
  if (!schema) return

  sellersDraft.value = (schema.parties?.sellers ?? []).map(toPartyDraft)
  buyersDraft.value = (schema.parties?.buyers ?? []).map(toPartyDraft)

  metadataDraft.location = schema.metadata?.location ?? ''
  metadataDraft.date = schema.metadata?.date ?? ''
  metadataDraft.language = (schema.metadata?.language ?? 'es') as LanguageCode

  propertyDraft.address = schema.property?.address ?? ''
  propertyDraft.registry = schema.property?.registry ?? ''
  propertyDraft.cargasText = (schema.property?.cargas ?? []).join('\n')
  propertyDraft.ibi = Number(schema.property?.ibi ?? 0)

  financialDraft.total_price = Number(schema.financial?.total_price ?? 0)
  financialDraft.arras_amount = Number(schema.financial?.arras_amount ?? 0)
  financialDraft.deadline = schema.financial?.deadline ?? ''
}

watch(() => props.contract, syncFromContract, { immediate: true, deep: true })

const addParty = (kind: 'sellers' | 'buyers') => {
  const target = kind === 'sellers' ? sellersDraft : buyersDraft
  target.value.push({ full_name: '', id_number: '' })
}

const removeParty = (kind: 'sellers' | 'buyers', index: number) => {
  const target = kind === 'sellers' ? sellersDraft : buyersDraft
  target.value.splice(index, 1)
}

const normalizeParties = (rows: PartyDraft[]) =>
  rows
    .map((row) => ({
      full_name: row.full_name.trim(),
      id_number: row.id_number.trim() || null
    }))
    .filter((row) => row.full_name || row.id_number)

const saveParties = (kind: 'sellers' | 'buyers') => {
  sectionError.value = ''
  const rows = kind === 'sellers' ? sellersDraft.value : buyersDraft.value
  const normalized = normalizeParties(rows)
  const invalid = normalized.some((row) => !row.full_name)
  if (invalid) {
    sectionError.value = 'Each party requires a full name. ID is optional.'
    return
  }
  save(`parties.${kind}`, normalized)
}

const saveMetadata = () => {
  sectionError.value = ''
  save('metadata', {
    location: metadataDraft.location.trim(),
    date: metadataDraft.date,
    language: metadataDraft.language
  })
}

const saveProperty = () => {
  sectionError.value = ''
  const cargas = propertyDraft.cargasText
    .split(/\n|,/)
    .map((entry) => entry.trim())
    .filter(Boolean)
  save('property', {
    address: propertyDraft.address.trim(),
    registry: propertyDraft.registry.trim(),
    cargas,
    ibi: Number(propertyDraft.ibi)
  })
}

const saveFinancial = () => {
  sectionError.value = ''
  save('financial', {
    total_price: Number(financialDraft.total_price),
    arras_amount: Number(financialDraft.arras_amount),
    deadline: financialDraft.deadline || null
  })
}
</script>

<template>
  <div class="card stack">
    <div class="tabs">
      <button v-for="t in tabs" :key="t" :class="{ active: modelValue === t }" @click="emit('update:modelValue', t)">
        {{ t }}
      </button>
    </div>

    <div v-if="modelValue === 'metadata'" class="grid-2">
      <label>
        Contract Location
        <input v-model="metadataDraft.location" placeholder="Example: Olèrdola" />
      </label>
      <label>
        Contract Date
        <input v-model="metadataDraft.date" type="date" />
      </label>
      <label>
        Contract Language
        <select v-model="metadataDraft.language">
          <option value="es">Spanish (canonical)</option>
          <option value="ca">Catalan</option>
          <option value="en">English</option>
        </select>
      </label>
      <div class="stack">
        <p class="hint">Example workflow: keep canonical data in Spanish and export translated variants.</p>
        <button class="primary" @click="saveMetadata">Save Metadata</button>
      </div>
    </div>

    <div v-else-if="modelValue === 'parties'" class="stack">
      <div class="party-section">
        <h3>Sellers</h3>
        <div v-if="!sellersDraft.length" class="hint">No sellers yet. Add one below.</div>
        <div v-for="(party, idx) in sellersDraft" :key="`seller-${idx}`" class="party-row">
          <label>
            Full Name
            <input v-model="party.full_name" placeholder="Example: Full Name" />
          </label>
          <label>
            ID Number
            <input v-model="party.id_number" placeholder="Example: ID ABC12345" />
          </label>
          <button class="danger" @click="removeParty('sellers', idx)">Remove</button>
        </div>
        <div class="inline-actions">
          <button class="secondary" @click="addParty('sellers')">Add Seller</button>
          <button class="primary" @click="saveParties('sellers')">Save Sellers</button>
        </div>
      </div>

      <div class="party-section">
        <h3>Buyers</h3>
        <div v-if="!buyersDraft.length" class="hint">No buyers yet. Add one below.</div>
        <div v-for="(party, idx) in buyersDraft" :key="`buyer-${idx}`" class="party-row">
          <label>
            Full Name
            <input v-model="party.full_name" placeholder="Example: Full Name" />
          </label>
          <label>
            ID Number
            <input v-model="party.id_number" placeholder="Example: ID ABC12345" />
          </label>
          <button class="danger" @click="removeParty('buyers', idx)">Remove</button>
        </div>
        <div class="inline-actions">
          <button class="secondary" @click="addParty('buyers')">Add Buyer</button>
          <button class="primary" @click="saveParties('buyers')">Save Buyers</button>
        </div>
      </div>
    </div>

    <div v-else-if="modelValue === 'property'" class="grid-2">
      <label>
        Property Address
        <input v-model="propertyDraft.address" placeholder="Example: Carrer Major 15, Olèrdola" />
      </label>
      <label>
        Registry Reference
        <input v-model="propertyDraft.registry" placeholder="Example: Reg. Vilafranca, Tomo 221, Libro 14, Finca 3345" />
      </label>
      <label>
        Charges / Liens
        <textarea
          v-model="propertyDraft.cargasText"
          rows="4"
          placeholder="Examples (one per line):&#10;Hipoteca Banco X - pendiente 12.000 EUR&#10;Sin cargas"
        />
      </label>
      <label>
        IBI (EUR/year)
        <input v-model.number="propertyDraft.ibi" type="number" step="0.01" placeholder="Example: 450.00" />
      </label>
      <button class="primary" @click="saveProperty">Save Property</button>
    </div>

    <div v-else-if="modelValue === 'financial'" class="grid-2">
      <label>
        Total Price (EUR)
        <input v-model.number="financialDraft.total_price" type="number" placeholder="Example: 45500" />
      </label>
      <label>
        Arras Amount (EUR)
        <input v-model.number="financialDraft.arras_amount" type="number" placeholder="Example: 4550" />
      </label>
      <label>
        Payment Deadline
        <input v-model="financialDraft.deadline" type="date" />
      </label>
      <label>
        Remaining Amount (derived)
        <input type="number" :value="financial.remaining_amount" disabled />
      </label>
      <button class="primary" @click="saveFinancial">Save Financial Terms</button>
    </div>

    <div v-else-if="modelValue === 'legal clauses'" class="stack">
      <p class="hint">
        Clause editing is available below. AI cannot override manually edited clauses unless explicitly allowed.
      </p>
    </div>

    <p v-if="sectionError" class="error">{{ sectionError }}</p>
  </div>
</template>
