<script setup lang="ts">
import { ref } from 'vue'
import { useContractStore } from '../stores/contractStore'

const props = defineProps<{ contractId: string }>()
const store = useContractStore()

const recording = ref(false)
const working = ref(false)
const transcript = ref('')
const updatesSummary = ref('')
const unsupported = ref(false)

let mediaRecorder: MediaRecorder | null = null
let streamRef: MediaStream | null = null
let chunks: BlobPart[] = []

const startRecording = async () => {
  unsupported.value = false
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
    unsupported.value = true
    return
  }

  try {
    streamRef = await navigator.mediaDevices.getUserMedia({ audio: true })
    chunks = []
    mediaRecorder = new MediaRecorder(streamRef)
    mediaRecorder.ondataavailable = (event: BlobEvent) => {
      if (event.data.size > 0) chunks.push(event.data)
    }
    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunks, { type: 'audio/webm' })
      working.value = true
      const result = await store.sendVoice(props.contractId, blob)
      working.value = false

      if (result) {
        transcript.value = result.transcript || ''
        updatesSummary.value = result.updates
          ?.map((item: any) => `${item.applied ? 'OK' : 'ERR'} ${item.path}${item.error ? ` (${item.error})` : ''}`)
          .join('\n')
      }
      streamRef?.getTracks().forEach((track) => track.stop())
      streamRef = null
    }
    mediaRecorder.start()
    recording.value = true
  } catch (_e) {
    unsupported.value = true
  }
}

const stopRecording = () => {
  if (mediaRecorder && recording.value) {
    mediaRecorder.stop()
  }
  recording.value = false
}
</script>

<template>
  <div class="card stack">
    <h3>Voice Agent Intake</h3>
    <p class="hint">
      Speak buyer/seller names, IDs, property details, price, arras, and deadline. The system transcribes and applies
      validated field updates.
    </p>
    <div class="inline-actions">
      <button v-if="!recording" class="secondary" :disabled="working" @click="startRecording">Start Recording</button>
      <button v-else class="danger" :disabled="working" @click="stopRecording">Stop Recording</button>
    </div>
    <p v-if="recording" class="hint">Recording...</p>
    <p v-if="working" class="hint">Transcribing and applying updates...</p>
    <p v-if="unsupported" class="error">Microphone/recording is not available in this browser.</p>
    <label v-if="transcript">
      Transcript
      <textarea :value="transcript" rows="4" readonly />
    </label>
    <label v-if="updatesSummary">
      Applied Updates
      <textarea :value="updatesSummary" rows="4" readonly />
    </label>
  </div>
</template>

