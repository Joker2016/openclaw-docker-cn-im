#!/usr/bin/env python3
"""完整测试套件：企业微信双模式配置同步"""
import os, sys, json, tempfile, subprocess

REPO = os.path.dirname(os.path.abspath(__file__))

def extract_python_code():
    with open(os.path.join(REPO, 'init.sh'), 'r') as f:
        content = f.read()
    marker = "CONFIG_FILE=\"$config_file\" python3 - <<'PYCODE'"
    start = content.find(marker)
    end = content.find("\nPYCODE", start)
    if start == -1 or end == -1:
        raise RuntimeError("无法找到Python代码块")
    return content[start + len(marker)+1 : end]

def run_sync(env_overrides):
    """在临时目录中运行配置同步，返回生成的配置"""
    tmpdir = tempfile.mkdtemp()
    cfg_path = os.path.join(tmpdir, 'openclaw.json')
    with open(cfg_path, 'w') as f:
        json.dump({}, f)

    env = {
        'CONFIG_FILE': cfg_path,
        'MODEL_ID': 'gpt-4o',
        'BASE_URL': 'http://test/v1',
        'API_KEY': 'test',
        'API_PROTOCOL': 'openai-completions',
        'HOME': tmpdir,
        'PATH': os.environ['PATH'],
    }
    env.update(env_overrides)

    code = extract_python_code()
    result = subprocess.run([sys.executable, '-c', code], env=env,
                            capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  stderr: {result.stderr[:500]}")
        return None, result.stdout, result.stderr

    with open(cfg_path) as f:
        config = json.load(f)
    
    import shutil; shutil.rmtree(tmpdir, ignore_errors=True)
    return config.get('channels', {}).get('wecom'), result.stdout, result.stderr

def check(condition, msg):
    if condition:
        print(f"  ✅ {msg}")
        return True
    else:
        print(f"  ❌ {msg}")
        return False

# ─── 测试用例 ───────────────────────────────────────────────────────────────

results = []

print("=" * 60)
print("企业微信双模式配置同步 - 完整测试套件")
print("=" * 60)

# ── 测试1：长连接模式（完整凭证）──────────────────────────────
print("\n【测试1】长连接模式（完整凭证）")
wecom, stdout, _ = run_sync({
    'WECOM_STREAM_MODE': 'true',
    'WECOM_BOT_ID': 'bot_abc123',
    'WECOM_BOT_SECRET': 'sec_xyz789',
    'WECOM_WS_URL': 'wss://openws.work.weixin.qq.com',
    'WECOM_HEARTBEAT_INTERVAL': '25000',
    'WECOM_RECONNECT_RETRIES': '3',
    'WECOM_DM_POLICY': 'open',
    'WECOM_ALLOW_FROM': '*',
    'WECOM_GROUP_POLICY': 'open',
})
ok = all([
    check(wecom is not None, "wecom 配置存在"),
    check(wecom.get('streamMode') is True, "streamMode=True"),
    check(wecom.get('botId') == 'bot_abc123', "botId 正确"),
    check(wecom.get('secret') == 'sec_xyz789', "secret 正确"),
    check(wecom.get('wsUrl') == 'wss://openws.work.weixin.qq.com', "wsUrl 正确"),
    check(wecom.get('heartbeatInterval') == 25000, "heartbeatInterval=25000"),
    check(wecom.get('reconnectRetries') == 3, "reconnectRetries=3"),
    check('default' not in wecom, "无 Webhook default 字段"),
    check('token' not in wecom, "无顶层 token 字段"),
    check('渠道同步: wecom (长连接模式)' in stdout, "日志输出正确"),
])
results.append(('长连接模式（完整凭证）', ok))

# ── 测试2：Webhook 模式 ─────────────────────────────────────────
print("\n【测试2】Webhook 模式")
wecom, stdout, _ = run_sync({
    'WECOM_STREAM_MODE': 'false',
    'WECOM_TOKEN': 'tok_111',
    'WECOM_ENCODING_AES_KEY': 'key_222',
    'WECOM_DM_POLICY': 'open',
    'WECOM_ALLOW_FROM': '*',
    'WECOM_GROUP_POLICY': 'open',
})
ok = all([
    check(wecom is not None, "wecom 配置存在"),
    check(wecom.get('streamMode') is False, "streamMode=False"),
    check(wecom.get('default', {}).get('token') == 'tok_111', "token 正确"),
    check(wecom.get('default', {}).get('encodingAesKey') == 'key_222', "encodingAesKey 正确"),
    check('botId' not in wecom, "无 botId 字段"),
    check('secret' not in wecom, "无 secret 字段"),
    check('渠道同步: wecom (Webhook模式)' in stdout, "日志输出正确"),
])
results.append(('Webhook 模式', ok))

# ── 测试3：长连接模式但凭证不完整 ─────────────────────────────
print("\n【测试3】长连接模式但凭证不完整（只有 BOT_ID，缺 SECRET）")
wecom, stdout, _ = run_sync({
    'WECOM_STREAM_MODE': 'true',
    'WECOM_BOT_ID': 'bot_abc123',
    # 故意不设 WECOM_BOT_SECRET
})
ok = all([
    check(wecom is None or not wecom.get('enabled'), "wecom 未被启用"),
    check('缺少 WECOM_BOT_ID 或 WECOM_BOT_SECRET' in stdout, "打印缺失警告"),
])
results.append(('长连接凭证不完整', ok))

# ── 测试4：无任何企业微信配置 ──────────────────────────────────
print("\n【测试4】无任何企业微信环境变量")
wecom, stdout, _ = run_sync({})
ok = check(wecom is None or not wecom.get('enabled'), "wecom 未启用（正确）")
results.append(('无企业微信配置', ok))

# ── 测试5：长连接模式使用默认 wsUrl ────────────────────────────
print("\n【测试5】长连接模式不指定 wsUrl（使用默认值）")
wecom, stdout, _ = run_sync({
    'WECOM_STREAM_MODE': 'true',
    'WECOM_BOT_ID': 'bot_x',
    'WECOM_BOT_SECRET': 'sec_y',
    # 不设 WECOM_WS_URL
})
ok = all([
    check(wecom is not None, "wecom 配置存在"),
    check(wecom.get('wsUrl') == 'wss://openws.work.weixin.qq.com', "wsUrl 使用默认值"),
    check(wecom.get('heartbeatInterval') == 30000, "heartbeatInterval 使用默认值 30000"),
    check(wecom.get('reconnectRetries') == 5, "reconnectRetries 使用默认值 5"),
])
results.append(('长连接默认值', ok))

# ── 测试6：Webhook 模式不设 WECOM_STREAM_MODE ──────────────────
print("\n【测试6】Webhook 模式（不设 WECOM_STREAM_MODE，向后兼容）")
wecom, stdout, _ = run_sync({
    # 不设 WECOM_STREAM_MODE
    'WECOM_TOKEN': 'tok_compat',
    'WECOM_ENCODING_AES_KEY': 'key_compat',
})
ok = all([
    check(wecom is not None, "wecom 配置存在"),
    check(wecom.get('streamMode') is False, "streamMode 默认为 False"),
    check(wecom.get('default', {}).get('token') == 'tok_compat', "token 正确"),
])
results.append(('Webhook 向后兼容', ok))

# ─── 汇总 ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("测试汇总:")
print("-" * 60)
all_pass = True
for name, passed in results:
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"  {name:<30} {status}")
    if not passed:
        all_pass = False
print("-" * 60)
if all_pass:
    print("🎉 全部 6 项测试通过！")
else:
    print("⚠️  有测试未通过，请检查")
sys.exit(0 if all_pass else 1)
