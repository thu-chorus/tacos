<template>
  <footer
    class="site-footer"
    :class="{ 'is-dark': dark, 'fixed-bottom': fixed }"
    role="contentinfo"
    aria-label="网站备案信息"
  >
    <a
      href="https://beian.miit.gov.cn/"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="工信部ICP备案查询 京ICP备2025146149号"
    >
      京ICP备2025146149号
    </a>
    <a
      href="https://beian.mps.gov.cn/#/query/webSearch?code=11010802046414"
      target="_blank"
      rel="noreferrer"
      aria-label="公安部备案查询 京公安网备11010802046414号"
    >
      京公安网备11010802046414号
    </a>
  </footer>
</template>

<script>
export default {
  name: 'SiteFooter',
  props: {
    dark: {
      type: Boolean,
      default: false
    },
    fixed: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style lang="scss" scoped>
.site-footer {
  width: 100%;
  text-align: center;
  padding: 12px 8px;
  font-size: 12px;
  color: #909399;
  z-index: 3;

  a {
    color: inherit;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

.site-footer.is-dark {
  color: rgba(255, 255, 255, 0.8);
}

.site-footer.fixed-bottom {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 8px;
}
</style>
