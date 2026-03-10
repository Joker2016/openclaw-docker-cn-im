#!/usr/bin/env python3
"""
企业微信长连接配置同步测试脚本
测试init.sh中的配置同步逻辑
"""

import os
import json
import tempfile
import subprocess
import sys

def test_wecom_stream_config():
    """测试长连接模式配置同步"""
    print("=== 测试1：长连接模式配置同步 ===")
    
    # 创建临时配置文件
    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    config_file.write('{}')
    config_file.close()
    
    # 设置环境变量
    env_vars = {
        'WECOM_STREAM_MODE': 'true',
        'WECOM_BOT_ID': 'bot_test_123456',
        'WECOM_BOT_SECRET': 'secret_test_abcdef',
        'WECOM_WS_URL': 'wss://openws.work.weixin.qq.com',
        'WECOM_HEARTBEAT_INTERVAL': '30000',
        'WECOM_RECONNECT_RETRIES': '5',
        'WECOM_DM_POLICY': 'open',
        'WECOM_ALLOW_FROM': '*',
        'WECOM_GROUP_POLICY': 'open',
        'CONFIG_FILE': config_file.name
    }
    
    # 导入测试环境的init.sh中的相关函数
    with open('init.sh', 'r') as f:
        content = f.read()
    
    # 提取Python配置同步代码部分
    py_code_start = content.find("CONFIG_FILE=\"$config_file\" python3 - <<'PYCODE'")
    py_code_end = content.find("PYCODE", py_code_start + 1)
    
    if py_code_start == -1 or py_code_end == -1:
        print("❌ 无法在init.sh中找到Python代码部分")
        return False
    
    # 提取Python代码
    py_code = content[py_code_start + len("CONFIG_FILE=\"$config_file\" python3 - <<'PYCODE'\n"):py_code_end].strip()
    
    # 在独立环境中执行同步逻辑
    test_env = os.environ.copy()
    test_env.update(env_vars)
    
    # 执行同步代码
    result = subprocess.run(
        [sys.executable, '-c', py_code],
        env=test_env,
        capture_output=True,
        text=True
    )
    
    print("输出:", result.stdout)
    print("错误:", result.stderr)
    
    if result.returncode != 0:
        print("❌ 长连接模式配置同步失败")
        return False
    
    # 读取生成的配置文件
    with open(config_file.name, 'r') as f:
        config = json.load(f)
    
    print("\n生成的配置:")
    wecom_config = config.get('channels', {}).get('wecom', {})
    print(json.dumps(wecom_config, indent=2, ensure_ascii=False))
    
    # 验证配置
    required_fields = ['streamMode', 'botId', 'secret', 'wsUrl', 'heartbeatInterval', 'reconnectRetries']
    for field in required_fields:
        if field not in wecom_config:
            print(f"❌ 缺少必要字段: {field}")
            return False
    
    if wecom_config['streamMode'] != True:
        print("❌ streamMode应为true")
        return False
    
    if wecom_config['botId'] != 'bot_test_123456':
        print("❌ botId不匹配")
        return False
    
    print("✅ 长连接模式配置同步测试通过")
    
    # 清理
    os.unlink(config_file.name)
    return True

def test_wecom_webhook_config():
    """测试Webhook模式配置同步"""
    print("\n=== 测试2：Webhook模式配置同步 ===")
    
    # 创建临时配置文件
    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    config_file.write('{}')
    config_file.close()
    
    # 设置环境变量
    env_vars = {
        'WECOM_STREAM_MODE': 'false',
        'WECOM_TOKEN': 'webhook_token_test',
        'WECOM_ENCODING_AES_KEY': 'webhook_key_test',
        'WECOM_DM_POLICY': 'open',
        'WECOM_ALLOW_FROM': '*',
        'WECOM_GROUP_POLICY': 'open',
        'CONFIG_FILE': config_file.name
    }
    
    with open('init.sh', 'r') as f:
        content = f.read()
    
    # 提取Python代码
    py_code_start = content.find("CONFIG_FILE=\"$config_file\" python3 - <<'PYCODE'")
    py_code_end = content.find("PYCODE", py_code_start + 1)
    
    if py_code_start == -1 or py_code_end == -1:
        print("❌ 无法在init.sh中找到Python代码部分")
        return False
    
    py_code = content[py_code_start + len("CONFIG_FILE=\"$config_file\" python3 - <<'PYCODE'\n"):py_code_end].strip()
    
    # 执行同步代码
    test_env = os.environ.copy()
    test_env.update(env_vars)
    
    result = subprocess.run(
        [sys.executable, '-c', py_code],
        env=test_env,
        capture_output=True,
        text=True
    )
    
    print("输出:", result.stdout)
    print("错误:", result.stderr)
    
    if result.returncode != 0:
        print("❌ Webhook模式配置同步失败")
        return False
    
    # 读取生成的配置文件
    with open(config_file.name, 'r') as f:
        config = json.load(f)
    
    print("\n生成的配置:")
    wecom_config = config.get('channels', {}).get('wecom', {})
    print(json.dumps(wecom_config, indent=2, ensure_ascii=False))
    
    # 验证配置
    if wecom_config.get('streamMode', False) != False:
        print("❌ streamMode应为false")
        return False
    
    default_account = wecom_config.get('default', {})
    if not isinstance(default_account, dict):
        print("❌ 缺少default账号配置")
        return False
    
    if default_account.get('token') != 'webhook_token_test':
        print("❌ token不匹配")
        return False
    
    if default_account.get('encodingAesKey') != 'webhook_key_test':
        print("❌ encodingAesKey不匹配")
        return False
    
    # 确保长连接相关字段不存在
    long_conn_fields = ['botId', 'secret', 'wsUrl', 'heartbeatInterval', 'reconnectRetries']
    for field in long_conn_fields:
        if field in wecom_config:
            print(f"❌ Webhook模式不应包含长连接字段: {field}")
            return False
    
    print("✅ Webhook模式配置同步测试通过")
    
    # 清理
    os.unlink(config_file.name)
    return True

def test_env_file_parsing():
    """测试.env文件解析"""
    print("\n=== 测试3：.env文件解析 ===")
    
    # 模拟Docker环境中的环境变量加载
    test_cases = [
        {
            'name': '长连接模式完整配置',
            'env_content': '''
WECOM_STREAM_MODE=true
WECOM_BOT_ID=bot_123
WECOM_BOT_SECRET=secret_456
WECOM_WS_URL=wss://openws.work.weixin.qq.com
WECOM_HEARTBEAT_INTERVAL=30000
WECOM_RECONNECT_RETRIES=5
            ''',
            'expected': {
                'streamMode': True,
                'botId': 'bot_123',
                'secret': 'secret_456',
                'wsUrl': 'wss://openws.work.weixin.qq.com',
                'heartbeatInterval': 30000,
                'reconnectRetries': 5
            }
        },
        {
            'name': 'Webhook模式配置',
            'env_content': '''
WECOM_STREAM_MODE=false
WECOM_TOKEN=token_123
WECOM_ENCODING_AES_KEY=key_456
            ''',
            'expected': {
                'streamMode': False,
                'token': 'token_123',
                'encodingAesKey': 'key_456'
            }
        },
        {
            'name': '混合配置（优先长连接）',
            'env_content': '''
WECOM_STREAM_MODE=true
WECOM_BOT_ID=bot_123
WECOM_BOT_SECRET=secret_456
WECOM_TOKEN=token_should_be_ignored
WECOM_ENCODING_AES_KEY=key_should_be_ignored
            ''',
            'expected': {
                'streamMode': True,
                'botId': 'bot_123',
                'secret': 'secret_456'
            }
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        
        # 模拟环境变量解析
        env_vars = {}
        for line in test_case['env_content'].strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        
        # 验证解析结果
        for key, expected_value in test_case['expected'].items():
            if key in ['heartbeatInterval', 'reconnectRetries']:
                actual_value = int(env_vars.get(key, 0))
            elif key == 'streamMode':
                actual_value = env_vars.get(key, 'false').lower() == 'true'
            else:
                actual_value = env_vars.get(key, '')
            
            if actual_value != expected_value:
                print(f"❌ 字段 {key}: 期望 {expected_value}, 实际 {actual_value}")
                all_passed = False
            else:
                print(f"✅ 字段 {key}: {actual_value}")
    
    if all_passed:
        print("✅ .env文件解析测试通过")
    else:
        print("❌ .env文件解析测试失败")
    
    return all_passed

def test_dockerfile_modifications():
    """测试Dockerfile修改"""
    print("\n=== 测试4：Dockerfile修改验证 ===")
    
    with open('Dockerfile', 'r') as f:
        dockerfile_content = f.read()
    
    # 检查关键修改
    checks = [
        {
            'name': 'WebSocket依赖安装',
            'pattern': 'npm install ws@\\^8\\.17\\.0 node-cache@\\^5\\.1\\.2 pino@\\^9\\.3\\.1',
            'required': True
        },
        {
            'name': '企业微信插件安装',
            'pattern': 'openclaw plugins install @sunnoy/wecom',
            'required': True
        },
        {
            'name': '依赖安装条件判断',
            'pattern': 'if \\[ -d "/home/node/\\.openclaw/extensions/wecom" \\]',
            'required': True
        }
    ]
    
    all_passed = True
    for check in checks:
        import re
        if check['required']:
            if re.search(check['pattern'], dockerfile_content):
                print(f"✅ {check['name']}: 检查通过")
            else:
                print(f"❌ {check['name']}: 未找到匹配模式")
                all_passed = False
        else:
            # 可选检查
            if re.search(check['pattern'], dockerfile_content):
                print(f"✅ {check['name']}: 存在")
            else:
                print(f"⚠️ {check['name']}: 不存在（可选）")
    
    if all_passed:
        print("✅ Dockerfile修改验证通过")
    else:
        print("❌ Dockerfile修改验证失败")
    
    return all_passed

def main():
    """主测试函数"""
    print("企业微信长连接配置框架测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(('长连接模式配置同步', test_wecom_stream_config()))
    test_results.append(('Webhook模式配置同步', test_wecom_webhook_config()))
    test_results.append(('.env文件解析', test_env_file_parsing()))
    test_results.append(('Dockerfile修改验证', test_dockerfile_modifications()))
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print("-" * 50)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:30} {status}")
        if not passed:
            all_passed = False
    
    print("-" * 50)
    if all_passed:
        print("🎉 所有测试通过！配置框架可正常工作")
        print("\n下一步:")
        print("1. 运行 ./push-wecom-fork.sh 推送到GitHub")
        print("2. 创建Pull Request合并到main分支")
        print("3. 构建新Docker镜像进行实际部署测试")
    else:
        print("⚠️ 部分测试失败，需要修复配置框架")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)