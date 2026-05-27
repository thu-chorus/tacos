#!/bin/bash

# TaCOS 代码格式化脚本
# 统一格式化 Python 和 JavaScript/Vue 代码

set -e

# 输出颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   TaCOS Code Formatting Script     ${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# 定位脚本目录和项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/tacos_backend"
FRONTEND_DIR="$PROJECT_ROOT/tacos_frontend"

# ========================================
# 格式化后端 Python 代码
# ========================================
echo -e "${YELLOW}[1/2] Formatting Python code with Black...${NC}"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# 检查 Black
if ! command -v black &> /dev/null; then
    echo -e "${YELLOW}Black is not installed. Installing...${NC}"
    pip install black
fi

# 检查 isort
if ! command -v isort &> /dev/null; then
    echo -e "${YELLOW}isort is not installed. Installing...${NC}"
    pip install isort
fi

# 使用 isort 排序导入
echo -e "${BLUE}Sorting Python imports with isort...${NC}"
isort . --profile black --skip-glob '*/migrations/*' --skip-glob '*/static/*' --skip-glob '*/media/*' || {
    echo -e "${RED}isort failed!${NC}"
    exit 1
}

# 使用 Black 格式化 Python
echo -e "${BLUE}Formatting Python files with Black...${NC}"
black . --exclude '/(\.git|\.venv|venv|env|__pycache__|\.pytest_cache|migrations|static|media)/' || {
    echo -e "${RED}Black formatting failed!${NC}"
    exit 1
}

echo -e "${GREEN}✓ Python code formatted successfully!${NC}"
echo ""

# ========================================
# 格式化前端 JavaScript/Vue 代码
# ========================================
echo -e "${YELLOW}[2/2] Formatting Frontend code with Prettier...${NC}"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# 使用 Prettier 格式化前端代码
echo -e "${BLUE}Formatting Vue/JavaScript files...${NC}"
npm run format || {
    echo -e "${RED}Prettier formatting failed!${NC}"
    exit 1
}

# 运行 ESLint 自动修复
echo -e "${BLUE}Running ESLint auto-fix...${NC}"
npm run lint || {
    echo -e "${YELLOW}Warning: ESLint found some issues that couldn't be auto-fixed${NC}"
}

echo -e "${GREEN}✓ Frontend code formatted successfully!${NC}"
echo ""

# ========================================
# 输出总结
# ========================================
cd "$SCRIPT_DIR"

echo -e "${BLUE}=====================================${NC}"
echo -e "${GREEN}✓ All code formatting completed!${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo -e "  - Python imports sorted with isort"
echo -e "  - Python code formatted with Black"
echo -e "  - Vue/JavaScript code formatted with Prettier"
echo -e "  - ESLint auto-fixes applied"
echo ""
echo -e "${GREEN}Done!${NC}"
