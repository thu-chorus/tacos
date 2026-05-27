import { toast } from 'vue-sonner'

export const notify = {
  success(message, opts = {}) {
    toast.success(message, { duration: 2500, ...opts })
  },
  error(message, opts = {}) {
    toast.error(message, { duration: 3500, ...opts })
  },
  info(message, opts = {}) {
    toast(message, { duration: 3000, ...opts })
  },
  warning(message, opts = {}) {
    toast.warning?.(message, { duration: 3000, ...opts }) ||
      toast(message, { duration: 3000, ...opts })
  },
  /**
   * Show a loading toast that persists until dismissed
   * @param {string} message - The message to display
   * @returns {{ close: () => void }} - Object with close method to dismiss the toast
   */
  loading(message) {
    const id = toast.loading(message, { duration: Infinity })
    return {
      close: () => toast.dismiss(id)
    }
  }
}

export default notify
