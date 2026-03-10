#!/bin/bash
# 企业微信长连接改造分支推送脚本

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 企业微信长连接改造分支推送脚本 ===${NC}"
echo

# 检查当前分支
BRANCH=$(git branch --show-current)
echo -e "当前分支: ${YELLOW}${BRANCH}${NC}"

if [ "$BRANCH" != "feat/wecom-websocket-stream-mode" ]; then
    echo -e "${RED}错误：当前不在 feat/wecom-websocket-stream-mode 分支${NC}"
    echo "请切换到正确分支：git checkout feat/wecom-websocket-stream-mode"
    exit 1
fi

# 显示修改内容
echo -e "${GREEN}修改文件清单：${NC}"
git status --short

echo
echo -e "${YELLOW}提交信息：${NC}"
git log --oneline -1

echo
echo -e "${GREEN}=== 推送选项 ===${NC}"
echo "1. 推送分支到远程仓库"
echo "2. 创建Pull Request（需要GitHub Token）"
echo "3. 导出补丁文件"
echo "4. 仅查看修改"
read -p "请选择操作 (1-4): " choice

case $choice in
    1)
        echo -e "${YELLOW}推送分支到远程仓库...${NC}"
        # 使用GitHub Token推送（需要配置）
        read -p "请输入GitHub Token: " token
        if [ -z "$token" ]; then
            echo -e "${RED}错误：需要GitHub Token${NC}"
            exit 1
        fi
        
        # 添加远程仓库凭据
        git remote set-url origin https://x-access-token:${token}@github.com/Joker2016/openclaw-docker-cn-im.git
        
        echo -e "${YELLOW}推送中...${NC}"
        git push -u origin feat/wecom-websocket-stream-mode
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 分支推送成功！${NC}"
            echo -e "分支URL: https://github.com/Joker2016/openclaw-docker-cn-im/tree/feat/wecom-websocket-stream-mode"
        else
            echo -e "${RED}❌ 推送失败${NC}"
        fi
        ;;
    2)
        echo -e "${YELLOW}创建Pull Request...${NC}"
        echo -e "请在GitHub网站手动创建PR："
        echo -e "URL: https://github.com/Joker2016/openclaw-docker-cn-im/compare/main...feat/wecom-websocket-stream-mode"
        echo
        echo -e "${GREEN}PR标题建议：${NC}"
        echo "feat: 添加企业微信智能机器人长连接（WebSocket）支持"
        echo
        echo -e "${GREEN}PR描述建议：${NC}"
        echo "## 功能描述"
        echo "添加企业微信智能机器人长连接（WebSocket）模式支持，相比传统Webhook模式有以下优势："
        echo "- 🚀 无需公网IP，适合内网环境部署"
        echo "- ⚡ 低延迟，消息实时性更好"
        echo "- 🔒 无需消息加解密，简化开发"
        echo "- 📦 内置心跳保活和断线重连"
        echo
        echo "## 配置方式"
        echo "在 `.env` 文件中设置："
        echo "```bash"
        echo "WECOM_STREAM_MODE=true"
        echo "WECOM_BOT_ID=your_bot_id"
        echo "WECOM_BOT_SECRET=your_secret"
        echo "```"
        echo
        echo "## 修改内容"
        echo "- 新增长连接模式环境变量配置"
        echo "- 更新init.sh同步逻辑支持双模式"
        echo "- 在Dockerfile中添加WebSocket依赖"
        echo "- 新增详细使用指南文档"
        ;;
    3)
        echo -e "${YELLOW}导出补丁文件...${NC}"
        # 创建补丁文件
        PATCH_FILE="wecom-websocket-upgrade-$(date +%Y%m%d).patch"
        git format-patch main --stdout > "$PATCH_FILE"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 补丁文件创建成功：${PATCH_FILE}${NC}"
            echo "文件大小:" $(wc -c < "$PATCH_FILE") "字节"
            echo "应用补丁：git apply $PATCH_FILE"
        else
            echo -e "${RED}❌ 补丁文件创建失败${NC}"
        fi
        ;;
    4)
        echo -e "${YELLOW}查看修改详情...${NC}"
        echo "=== 文件修改详情 ==="
        git diff --stat main
        echo
        echo "=== 关键修改预览 ==="
        git diff --no-ext-diff main -- .env.example init.sh Dockerfile
        ;;
    *)
        echo -e "${RED}无效的选择${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}=== 操作完成 ===${NC}"
echo "详细文档："
echo "- WECOM-WEBSOCKET-UPGRADE.md - 技术改造方案"
echo "- WECOM-WEBSOCKET-GUIDE.md - 用户使用指南"
echo "- CHANGES-SUMMARY.md - 修改总结"