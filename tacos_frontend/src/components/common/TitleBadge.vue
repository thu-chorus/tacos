<template>
  <el-tooltip :content="tooltipContent" placement="top" effect="dark" :show-after="150">
    <span class="title-badge" :style="badgeStyle" tabindex="0" @keyup.enter.stop @click.stop>
      <i v-if="iconName" :class="iconClass" :style="iconStyle" />
      <slot>{{ title?.name }}</slot>
      <sup v-if="badge.enabled" class="badge-dot" :style="badgeStyleObj"></sup>
    </span>
  </el-tooltip>
</template>

<script>
export default {
  name: 'TitleBadge',
  props: {
    title: { type: Object, required: true }
  },
  computed: {
    tooltipContent() {
      const lines = []
      // 兼容两种结构：
      const desc =
        this.title?.description || (this.title?.title && this.title.title.description) || ''
      if (desc) {
        lines.push(desc)
      }
      const awarded = this.title?.awarded_at
      if (awarded) {
        lines.push(`授予日期：${awarded}`)
      }
      return lines.join('\n') || '称号'
    },
    appearance() {
      return this.title?.appearance || {}
    },
    icon() {
      return this.appearance.icon || {}
    },
    iconName() {
      return this.icon.name
    },
    iconClass() {
      // 默认使用 Element Plus 图标集类名约定；也可改为自定义映射
      const set = this.icon.set || 'ep'
      const name = this.icon.name || ''
      return set && name ? `${set} icon-${name}` : ''
    },
    iconStyle() {
      return {
        fontSize: `${this.icon.size_px || 14}px`,
        color: this.icon.color || '#fff',
        marginRight: (this.icon.position || 'left') === 'left' ? `${this.icon.gap_px || 6}px` : 0,
        marginLeft: (this.icon.position || 'left') === 'right' ? `${this.icon.gap_px || 6}px` : 0
      }
    },
    gradient() {
      const g = this.appearance.gradient || {}
      if (!g.enabled) {
        return null
      }
      const angle = g.angle_deg || 0
      const stops = Array.isArray(g.stops) ? g.stops : []
      const stopStr = stops.map(s => `${s.color} ${s.position_pct || 0}%`).join(', ')
      return `linear-gradient(${angle}deg, ${stopStr})`
    },
    border() {
      return this.appearance.border || {}
    },
    padding() {
      return this.appearance.padding_px || { top: 4, right: 10, bottom: 4, left: 10 }
    },
    font() {
      return this.appearance.font || {}
    },
    shadow() {
      const s = this.appearance.shadow || {}
      return s.enabled ? s.value || '0 2px 8px rgba(0,0,0,.12)' : 'none'
    },
    badge() {
      return this.appearance.badge || { enabled: false }
    },
    badgeStyleObj() {
      return {
        backgroundColor: this.badge.bg_color || '#ff4d4f',
        color: this.badge.text_color || '#fff',
        borderColor: this.badge.border_color || '#fff'
      }
    },
    badgeStyle() {
      const bg = this.gradient || this.appearance.bg_color || '#409EFF'
      return {
        background: bg,
        color: this.appearance.text_color || '#fff',
        borderStyle: this.border.style || 'solid',
        borderWidth: `${this.border.width_px || 0}px`,
        borderColor: this.border.color || 'transparent',
        borderRadius: `${this.border.radius_px || 16}px`,
        padding: `${this.padding.top}px ${this.padding.right}px ${this.padding.bottom}px ${this.padding.left}px`,
        boxShadow: this.shadow,
        fontSize: `${this.font.size_px || 12}px`,
        fontWeight: this.font.weight || 500,
        fontFamily: this.font.family,
        textTransform: this.font.uppercase ? 'uppercase' : 'none',
        fontStyle: this.font.italic ? 'italic' : 'normal',
        lineHeight: this.font.line_height || 1.2,
        letterSpacing: `${this.font.letter_spacing_px || 0}px`,
        display: 'inline-flex',
        alignItems: 'center'
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.title-badge {
  position: relative;
}
.badge-dot {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid;
}
</style>
