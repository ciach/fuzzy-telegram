import { defineStore } from 'pinia'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const useContractStore = defineStore('contracts', {
  state: () => ({
    contract: null as any,
    logs: [] as any[],
    aiInteractions: [] as any[],
    voiceLastResult: null as any,
    loading: false,
    error: ''
  }),
  actions: {
    async createContract(language = 'es', location = 'Barcelona') {
      this.loading = true
      this.error = ''
      try {
        const response = await fetch(`${API_BASE}/contracts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ language, location })
        })
        if (!response.ok) throw new Error(await response.text())
        const data = await response.json()
        this.contract = data
        return data
      } catch (err: any) {
        this.error = err.message || 'Failed to create contract'
        throw err
      } finally {
        this.loading = false
      }
    },
    async loadContract(id: string) {
      const response = await fetch(`${API_BASE}/contracts/${id}`)
      if (response.ok) this.contract = await response.json()
    },
    async updateField(id: string, payload: { path: string; value: unknown }) {
      this.error = ''
      const response = await fetch(`${API_BASE}/contracts/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!response.ok) {
        this.error = await response.text()
        return
      }
      this.contract = await response.json()
      await this.loadLogs(id)
    },
    async sendChat(id: string, message: string) {
      this.error = ''
      const response = await fetch(`${API_BASE}/contracts/${id}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, allow_manual_clause_override: false })
      })
      if (!response.ok) {
        this.error = await response.text()
        return
      }
      const data = await response.json()
      if (data.contract) this.contract = data.contract
      await this.loadLogs(id)
      await this.loadAiInteractions(id)
    },
    async loadLogs(id: string) {
      const response = await fetch(`${API_BASE}/contracts/${id}/logs`)
      if (response.ok) this.logs = await response.json()
    },
    async loadAiInteractions(id: string) {
      const response = await fetch(`${API_BASE}/contracts/${id}/ai-interactions`)
      if (response.ok) this.aiInteractions = await response.json()
    },
    async exportDocument(id: string, kind: 'pdf' | 'docx') {
      this.error = ''
      const response = await fetch(`${API_BASE}/contracts/${id}/export/${kind}`, {
        method: 'POST'
      })
      if (!response.ok) {
        this.error = await response.text()
        return
      }
      const blob = await response.blob()
      const ext = kind === 'pdf' ? 'pdf' : 'docx'
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `arras-${id}.${ext}`
      a.click()
      URL.revokeObjectURL(url)
    },
    async sendVoice(id: string, audioBlob: Blob) {
      this.error = ''
      const formData = new FormData()
      formData.append('audio_file', audioBlob, 'voice.webm')

      const response = await fetch(`${API_BASE}/contracts/${id}/voice-intake`, {
        method: 'POST',
        body: formData
      })
      if (!response.ok) {
        this.error = await response.text()
        return null
      }
      const data = await response.json()
      this.voiceLastResult = data
      if (data.contract) this.contract = data.contract
      await this.loadLogs(id)
      await this.loadAiInteractions(id)
      return data
    }
  }
})
