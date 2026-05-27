# 静态资源目录

此目录用于存放需要在构建时直接复制到输出目录的静态文件。

## 图标文件

请将以下文件放置在此目录中：

- `favicon.ico` - 网站图标 (建议尺寸: 16x16, 32x32, 48x48)
- `icon.png` - Apple Touch 图标和其他用途的图标 (建议尺寸: 192x192 或 512x512)

## 文件说明

- `favicon.ico`: 浏览器标签页显示的图标
- `icon.png`: 用于 Apple Touch 图标、PWA 图标等

## 注意事项

1. 这些文件会被直接复制到构建输出的根目录
2. 文件名不会添加 hash，确保浏览器缓存和引用的一致性
3. 确保图标文件符合相应的尺寸要求

## 生成图标文件的工具推荐

- [Favicon Generator](https://favicon.io/)
- [RealFaviconGenerator](https://realfavicongenerator.net/)
- [Favicon.ico Generator](https://www.favicon-generator.org/)
