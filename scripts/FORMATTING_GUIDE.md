# Code Formatting Guide

## 概述

本项目使用自动化工具来保持代码风格的一致性：
- **Python**: Black + isort
- **JavaScript/Vue**: Prettier + ESLint

## 快速使用

### 方式一：使用 pre-commit 实现提交前自动格式化（推荐）

项目根目录已提供 `.pre-commit-config.yaml`，可在本地安装 Git 钩子，使每次 `git commit` 前自动运行格式化：

```bash
# 一次性安装 pre-commit（建议在 Python 虚拟环境中）
pip install pre-commit

# 安装 Git 钩子（在仓库根目录执行）
pre-commit install

# 可选：首次运行对全仓库执行检查/修复
pre-commit run --all-files
```

上述钩子会自动执行：
- 后端（Python）：isort 排序导入、Black 格式化（读取 `tacos_backend/pyproject.toml` 配置）
- 前端（Vue/JS）：Prettier 格式化 `tacos_frontend/src/` 下的文件
- 通用：修复行尾空白、文件末行换行、检查合并冲突标记等

注意：pre-commit 与 CI 无关，仅在本地开发者环境触发。建议所有开发者都执行一次 `pre-commit install`。

### 方式一：使用格式化脚本（推荐）

```bash
chmod +x format_code.sh
./scripts/format_code.sh
```

### 方式三：单独格式化

#### 格式化 Python 代码
```bash
cd tacos_backend

# 格式化所有 Python 文件
black .

# 排序 imports
isort .
```

#### 格式化前端代码
```bash
cd tacos_frontend

# 格式化所有文件
npm run format

# 运行 ESLint 修复
npm run lint
```

## 配置文件

### Python (Black)
配置文件: `tacos_backend/pyproject.toml`

主要配置：
- 行长度: 88 字符
- Python 版本: 3.11+
- 排除目录: migrations, static, media 等

### Python (isort)
配置文件: `tacos_backend/pyproject.toml`

主要配置：
- 与 Black 兼容
- Django 项目优化
- 自动分组导入语句

### JavaScript/Vue (Prettier)
配置文件: `tacos_frontend/.prettierrc`

主要配置：
- 不使用分号
- 使用单引号
- 2 空格缩进
- 行长度: 100 字符

## 安装依赖

### Python 工具
```bash
cd tacos_backend
pip install black isort
```

或者安装所有依赖：
```bash
pip install -r requirements.txt
```

### 前端工具
```bash
cd tacos_frontend
npm install
```

## 编辑器集成

### VS Code

1. 安装扩展：
   - Python: ms-python.black-formatter
   - Prettier: esbenp.prettier-vscode
   - ESLint: dbaeumer.vscode-eslint

2. 配置保存时自动格式化（可选）：
   在 `.vscode/settings.json` 中添加：
   ```json
   {
     "editor.formatOnSave": true,
     "python.formatting.provider": "black",
     "[python]": {
       "editor.defaultFormatter": "ms-python.black-formatter",
       "editor.formatOnSave": true,
       "editor.codeActionsOnSave": {
         "source.organizeImports": true
       }
     },
     "[javascript]": {
       "editor.defaultFormatter": "esbenp.prettier-vscode"
     },
     "[vue]": {
       "editor.defaultFormatter": "esbenp.prettier-vscode"
     }
   }
   ```

## CI/CD 集成

在 CI 流程中添加代码检查：

### Python 检查
```bash
black --check .
isort --check-only .
```

### 前端检查
```bash
npm run format -- --check
npm run lint
```

## 最佳实践

1. **提交前格式化**: 在提交代码前运行格式化脚本，或者安装 pre-commit 钩子，让 Git 在每次提交前自动运行格式化
2. **配置编辑器**: 配置编辑器在保存时自动格式化
3. **团队协作**: 确保所有团队成员使用相同的配置
4. **不要手动格式化**: 让工具处理所有格式化工作

## 常见问题

### Q: Black 和我的编辑器配置冲突？
A: 禁用编辑器的 Python 格式化，使用 Black 作为唯一的格式化工具。

### Q: 如何忽略某些文件？
A: 编辑 `pyproject.toml` (Python) 或 `.prettierignore` (前端) 文件。

### Q: 格式化破坏了我的代码？
A: Black 和 Prettier 都经过充分测试，不会改变代码逻辑。如果发现问题，请检查原代码是否有语法错误。

## 更多信息

- [Black 文档](https://black.readthedocs.io/)
- [isort 文档](https://pycqa.github.io/isort/)
- [Prettier 文档](https://prettier.io/)
- [ESLint 文档](https://eslint.org/)
