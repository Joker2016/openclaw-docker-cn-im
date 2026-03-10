#!/bin/bash
# 简单测试init.sh的配置同步功能

echo "=== 测试企业微信长连接配置同步 ==="

# 创建测试用临时目录
TEST_DIR=$(mktemp -d)
echo "测试目录: $TEST_DIR"

# 创建基础配置文件
cat > "$TEST_DIR/openclaw.json" <<EOF
{
  "channels": {},
  "plugins": {
    "entries": {},
    "installs": {}
  }
}
EOF

# 设置环境变量（长连接模式）
export WECOM_STREAM_MODE=true
export WECOM_BOT_ID=bot_test_123
export WECOM_BOT_SECRET=secret_test_456
export WECOM_WS_URL=wss://openws.work.weixin.qq.com
export WECOM_HEARTBEAT_INTERVAL=30000
export WECOM_RECONNECT_RETRIES=5
export WECOM_DM_POLICY=open
export WECOM_ALLOW_FROM=*
export WECOM_GROUP_POLICY=open
export CONFIG_FILE="$TEST_DIR/openclaw.json"

echo "环境变量已设置"
echo "WECOM_STREAM_MODE=$WECOM_STREAM_MODE"
echo "WECOM_BOT_ID=$WECOM_BOT_ID"

# 从init.sh中提取Python配置同步代码
python_code=$(grep -A 1000 "CONFIG_FILE=\"\$config_file\" python3 - <<'PYCODE'" init.sh | grep -B 1000 "^PYCODE$" | tail -n +2 | head -n -1)

if [ -z "$python_code" ]; then
    echo "❌ 无法提取Python配置代码"
    exit 1
fi

echo "执行配置同步..."
echo "$python_code" | python3

if [ $? -eq 0 ]; then
    echo "✅ 配置同步执行成功"
    
    # 查看生成的配置
    echo -e "\n生成的配置:"
    cat "$TEST_DIR/openclaw.json" | python3 -m json.tool | grep -A 20 '"wecom"'
    
    # 验证配置
    if python3 -c "
import json
with open('$TEST_DIR/openclaw.json') as f:
    config = json.load(f)

wecom = config.get('channels', {}).get('wecom', {})
if not wecom:
    print('❌ 缺少wecom配置')
    exit(1)

if wecom.get('streamMode') != True:
    print('❌ streamMode应为true')
    exit(1)

if wecom.get('botId') != 'bot_test_123':
    print('❌ botId不匹配')
    exit(1)

if wecom.get('secret') != 'secret_test_456':
    print('❌ secret不匹配')
    exit(1)

print('✅ 长连接配置验证通过')
"; then
        echo "✅ 配置验证成功"
    else
        echo "❌ 配置验证失败"
    fi
else
    echo "❌ 配置同步执行失败"
fi

# 清理
rm -rf "$TEST_DIR"
echo -e "\n测试完成"