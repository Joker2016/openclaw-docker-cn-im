# 企业微信智能机器人长连接（WebSocket）改造方案

## 概述

将 `@sunnoy/wecom` 插件从 HTTP Webhook 模式升级为支持企业微信官方智能机器人长连接（WebSocket）模式，同时保持向后兼容。

## 技术架构

### 当前架构 (HTTP Webhook)
```
用户消息 → 企业微信 → HTTP POST → 公网URL → WeCom插件 → OpenClaw
                              ↑
                          需要公网IP
```

### 目标架构 (WebSocket长连接)
```
用户消息 → 企业微信 → WebSocket推送 → WeCom插件(WebSocket客户端) → OpenClaw
                                    ↑
                                 心跳保活(30s ping)
```

## 环境变量配置

### 新增环境变量
```bash
# 模式开关
WECOM_STREAM_MODE=true  # 启用长连接模式（默认false）

# 长连接专用凭证（不同于Webhook）
WECOM_BOT_ID=bot_xxxxxx           # 智能机器人BotID
WECOM_BOT_SECRET=secret_xxxxxx    # 长连接专用Secret

# WebSocket连接配置
WECOM_WS_URL=wss://openws.work.weixin.qq.com  # 可选，默认官方地址

# 心跳配置
WECOM_HEARTBEAT_INTERVAL=30000    # 心跳间隔(ms)，默认30秒
WECOM_RECONNECT_RETRIES=5         # 重连次数，默认5次
```

### 保留现有环境变量（兼容Webhook）
```bash
# Webhook模式专用
WECOM_TOKEN=xxx
WECOM_ENCODING_AES_KEY=xxx

# 通用配置
WECOM_DM_POLICY=open
WECOM_ALLOW_FROM=*
WECOM_GROUP_POLICY=open
```

## 代码结构改造

### 1. 新增核心服务类 `WeComStreamService`

```typescript
// src/services/wecom-stream-service.ts
export class WeComStreamService {
  // 核心属性
  private wsClient: WebSocket;
  private botId: string;
  private secret: string;
  private heartbeatInterval: NodeJS.Timeout;
  private connectionStatus: 'disconnected' | 'connecting' | 'connected';
  private messageQueue: Map<string, PendingMessage>;
  
  // 生命周期管理
  async connect(): Promise<void>;          // 建立WebSocket连接
  async disconnect(): Promise<void>;       // 断开连接
  async reconnect(): Promise<boolean>;     // 断线重连
  
  // 消息处理
  async sendSubscribe(): Promise<void>;    // 发送订阅请求
  async replyMessage(): Promise<void>;     // 回复消息
  async sendHeartbeat(): Promise<void>;    // 发送心跳
  
  // 事件处理
  private handleMessage(data: WebSocket.Data): Promise<void>;
  private handleOpen(): Promise<void>;
  private handleClose(code: number, reason: string): Promise<void>;
  private handleError(error: Error): Promise<void>;
}
```

### 2. 新增适配器层 `WeComAdapter`

```typescript
// src/services/wecom-adapter.ts
export class WeComAdapter {
  private webhookService: WeComWebhookService;
  private streamService: WeComStreamService;
  private currentMode: 'webhook' | 'stream';
  
  // 根据环境变量自动选择模式
  constructor(config: WeComConfig) {
    this.currentMode = config.streamMode ? 'stream' : 'webhook';
    
    if (this.currentMode === 'stream') {
      this.streamService = new WeComStreamService(config);
    } else {
      this.webhookService = new WeComWebhookService(config);
    }
  }
  
  // 统一接口
  async start(): Promise<void>;
  async handleIncomingMessage(rawMessage: any): Promise<OpenClawMessage>;
  async sendResponse(originalMessage: OpenClawMessage, response: string): Promise<void>;
}
```

### 3. 配置管理更新

```typescript
// src/config/wecom-config.ts
export interface WeComStreamConfig {
  streamMode: boolean;
  botId?: string;
  secret?: string;
  wsUrl?: string;
  heartbeatInterval?: number;
  reconnectRetries?: number;
}

export interface WeComWebhookConfig {
  token?: string;
  encodingAesKey?: string;
  // ... 现有配置
}

export type WeComConfig = WeComStreamConfig & WeComWebhookConfig & {
  enabled: boolean;
  dmPolicy: string;
  allowFrom: string[];
  groupPolicy: string;
};
```

## Dockerfile 更新

```dockerfile
# 在现有Dockerfile中添加新依赖
RUN npm install @wecom/aibot-node-sdk ws node-cache pino

# 或者作为插件依赖在插件安装阶段添加
RUN timeout 300 openclaw plugins install @sunnoy/wecom || true && \
    cd /home/node/.openclaw/extensions/wecom && \
    npm install @wecom/aibot-node-sdk ws node-cache pino --save
```

## init.sh 同步逻辑更新

在 `sync_config_with_env()` 函数的Python代码中，需要添加长连接配置同步：

```python
def sync_wecom_stream_config(config, env):
    wecom = config.get('channels', {}).get('wecom', {})
    
    stream_mode = env.get('WECOM_STREAM_MODE', 'false').lower() == 'true'
    bot_id = env.get('WECOM_BOT_ID')
    secret = env.get('WECOM_BOT_SECRET')
    
    if stream_mode and bot_id and secret:
        # 长连接配置
        wecom.update({
            'streamMode': True,
            'botId': bot_id,
            'secret': secret,
            'wsUrl': env.get('WECOM_WS_URL', 'wss://openws.work.weixin.qq.com'),
            'heartbeatInterval': int(env.get('WECOM_HEARTBEAT_INTERVAL', '30000')),
            'reconnectRetries': int(env.get('WECOM_RECONNECT_RETRIES', '5'))
        })
        print('✅ 企业微信长连接配置已同步')
    elif not stream_mode:
        # Webhook配置（保持现有逻辑）
        wecom.update({
            'streamMode': False
        })
```

同时需要更新渠道同步规则：

```python
# sync_rules 数组中更新企业微信规则
(
    ['WECOM_TOKEN', 'WECOM_ENCODING_AES_KEY'],  # Webhook模式要求
    ['WECOM_BOT_ID', 'WECOM_BOT_SECRET'],       # 长连接模式要求（可选）
    'wecom', 
    sync_wecom,
    plugin_info
)
```

## 企业微信管理后台配置

### 1. 创建智能机器人
1. 登录企业微信管理后台
2. 进入「应用管理」→「智能机器人」
3. 点击「创建机器人」
4. 设置机器人名称和头像

### 2. 获取长连接凭证
1. 在机器人配置页面选择「API模式」
2. 选择「长连接」方式
3. 获取 `BotID` 和 `Secret`
4. **注意**：此 `Secret` 不同于Webhook的 `EncodingAESKey`

### 3. 配置对比

| 配置项 | Webhook模式 | WebSocket长连接模式 |
|--------|------------|-------------------|
| 凭证类型 | Token + EncodingAESKey | BotID + Secret |
| 连接方式 | HTTP回调 | WebSocket长连接 |
| 公网需求 | 需要公网URL | 无需公网IP |
| 加解密 | 需要 | 无需 |
| 心跳维护 | 不需要 | 需要(30s间隔) |

## 测试验证方案

### 1. 单元测试
```bash
# 测试长连接服务
npm test -- --testPathPattern=wecom-stream-service

# 测试适配器
npm test -- --testPathPattern=wecom-adapter

# 测试配置解析
npm test -- --testPathPattern=wecom-config
```

### 2. 集成测试
```bash
# 启动测试服务器
docker-compose -f docker-compose.test.yml up

# 运行集成测试
npm run test:integration -- --testNamePattern="企业微信长连接"
```

### 3. 手动验证步骤
1. 配置环境变量 `WECOM_STREAM_MODE=true`
2. 设置正确的 `WECOM_BOT_ID` 和 `WECOM_BOT_SECRET`
3. 启动容器 `docker-compose up`
4. 查看日志确认WebSocket连接成功
5. 在企业微信中向机器人发送消息
6. 验证消息接收和回复功能

## 错误处理和监控

### 1. 错误类型
- 连接失败：网络问题、凭证错误
- 心跳超时：连接断开
- 消息处理失败：格式错误、业务逻辑异常
- 重连失败：达到最大重试次数

### 2. 监控指标
```typescript
interface WeComStreamMetrics {
  connectionStatus: string;      // 连接状态
  lastHeartbeatTime: number;     // 最后心跳时间
  totalMessagesReceived: number; // 接收消息总数
  totalMessagesSent: number;     // 发送消息总数
  reconnectCount: number;        // 重连次数
  averageResponseTime: number;   // 平均响应时间(ms)
}
```

### 3. 日志格式
```
[2026-03-10T13:45:00.123Z] INFO  WeComStreamService - WebSocket连接已建立
[2026-03-10T13:45:30.456Z] DEBUG WeComStreamService - 心跳发送成功
[2026-03-10T13:46:15.789Z] INFO  WeComStreamService - 收到消息: msgid=msg_123456
[2026-03-10T13:46:16.012Z] ERROR WeComStreamService - 连接断开，开始重连 (尝试1/5)
```

## 回滚方案

### 1. 快速回滚
```bash
# 切换到Webhook模式
export WECOM_STREAM_MODE=false
export WECOM_TOKEN=xxx
export WECOM_ENCODING_AES_KEY=xxx

# 重启容器
docker-compose down && docker-compose up -d
```

### 2. 版本回退
```bash
# 切换到上一个稳定版本
git checkout v1.2.0
docker-compose build
docker-compose up -d
```

### 3. 监控告警
设置关键指标告警：
- 连接状态持续断开 > 5分钟
- 消息接收成功率 < 95%
- 平均响应时间 > 3000ms

## 部署时间线

### 阶段1：开发测试 (3天)
- Day 1-2: 实现核心WebSocket服务
- Day 3: 集成测试和bug修复

### 阶段2：预发布测试 (2天)
- Day 1: 部署到测试环境
- Day 2: 完整功能测试和性能测试

### 阶段3：生产部署 (1天)
- 分批次灰度发布
- 监控关键指标
- 准备快速回滚方案

## 资源需求

### 开发资源
- 前端开发：1人 (2天)
- 后端开发：1人 (3天)
- 测试：1人 (2天)

### 技术依赖
- Node.js 18+
- WebSocket客户端库 (`ws`)
- 企业微信官方SDK (`@wecom/aibot-node-sdk`)
- 日志和监控系统

## 成功标准

### 功能标准
- [ ] WebSocket连接稳定建立
- [ ] 心跳机制正常工作
- [ ] 消息收发功能完整
- [ ] 断线自动重连
- [ ] 与现有系统完全兼容

### 性能标准
- [ ] 消息接收延迟 < 1秒
- [ ] 连接成功率 > 99.9%
- [ ] 系统资源占用合理

### 可靠性标准
- [ ] 7x24小时稳定运行
- [ ] 故障自动恢复
- [ ] 完整的监控告警

---

**最后更新**: 2026-03-10  
**负责人**: jokerxliu  
**状态**: 开发中