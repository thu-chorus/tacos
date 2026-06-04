<template>
  <button class="btn-modern ghost sm-btn back-btn" @click="handleClick" :aria-label="text">
    <i-lucide-arrow-left class="btn-icon" />
    <span>{{ text }}</span>
  </button>
</template>

<script>
import { useRouter } from 'vue-router'

export default {
  name: 'BackButton',
  props: {
    text: {
      type: String,
      default: '返回'
    },
    to: {
      type: String,
      default: ''
    }
  },
  emits: ['click'],
  setup(props) {
    const router = useRouter()

    const handleClick = () => {
      // 如果指定了路由，导航到该路由
      if (props.to) {
        router.push(props.to)
      } else {
        // 默认返回上一页
        router.back()
      }
    }

    return {
      handleClick
    }
  }
}
</script>

<style lang="scss" scoped>
.back-btn {
  border-color: var(--border);
  background: transparent;
  color: #374151;
  transition:
    transform 120ms ease,
    box-shadow 200ms ease;

  &:hover {
    background: #d4d8de60;
  }

  &:active {
    transform: translateY(1px) scale(0.98);
  }
}
</style>
