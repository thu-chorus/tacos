import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// Vite 配置文档：https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: '@use \'src/assets/styles/variables.scss\' as *; @use \'src/assets/styles/mixins.scss\' as *;'
      }
    }
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          // 保持 favicon.ico 和 icon.png 在根目录，不添加 hash
          if (assetInfo.name === 'favicon.ico' || assetInfo.name === 'icon.png') {
            return '[name].[ext]'
          }
          return '[ext]/[name]-[hash].[ext]'
        }
      }
    }
  },
  // 确保 public 目录中的文件被复制到构建输出
  publicDir: 'public'
})
