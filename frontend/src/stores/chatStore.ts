import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as Array<{ role: 'user' | 'assistant'; text: string }>
  }),
  actions: {
    add(role: 'user' | 'assistant', text: string) {
      this.messages.push({ role, text })
    }
  }
})
