# 企业微信长连接改造 - 修改总结

## 分支信息
- **分支名称**: `feat/wecom-websocket-stream-mode`
- **基础分支**: `main`
- **提交ID**: `d2d0eed`

## 修改文件

### 1. `.env.example` - 环境变量示例
**修改内容**：
- 新增长连接模式环境变量说明
- 将企业微信配置分为三个部分：
  1. Webhook模式（传统）
  2. 长连接模式（WebSocket）
  3. 多账号JSON配置

**关键新增**：
```bash
# 长连接模式配置
WECOM_STREAM_MODE=false
WECOM_BOT_ID=
WECOM_BOT_SECRET=
WECOM_WS_URL=wss://openws.work.weixin.qq.com
WECOM_HEARTBEAT_INTERVAL=30000
WECOM_RECONNECT_RETRIES=5
```

### 2. `init.sh` - 初始化脚本
**修改内容**：
- 新增 `sync_wecom_stream_config()` 函数处理长连接配置
- 更新 `sync_wecom()` 函数支持双模式
- 添加长连接配置字段：
  - `streamMode`: true/false
  - `botId`: 智能机器人BotID
  - `secret`: 长连接专用Secret
  - `wsUrl`: WebSocket连接地址
  - `heartbeatInterval`: 心跳间隔
  - `reconnectRetries`: 重连次数

**配置逻辑**：
- 当 `WECOM_STREAM_MODE=true` 且配置了 `WECOM_BOT_ID` 和 `WECOM_BOT_SECRET` 时，启用长连接模式
- 否则使用Webhook模式
- 自动清理不相关的配置字段避免混淆

### 3. `Dockerfile` - 容器构建文件
**修改内容**：
- 在安装 `@sunnoy/wecom` 插件后，自动安装WebSocket依赖包：
  ```dockerfile
  npm install ws@^8.17.0 node-cache@^5.1.2 pino@^9.3.1
  ```

### 4. 新增文档文件

#### `WECOM-WEBSOCKET-UPGRADE.md`
- 详细的技术改造方案
- 包含代码结构、接口设计、实现步骤
- 风险评估和回滚方案
- 开发时间线规划

#### `WECOM-WEBSOCKET-GUIDE.md`
- 用户使用指南
- 企业微信管理后台配置步骤
- Docker环境配置说明
- 故障排除和监控指南
- 最佳实践建议

## 配置对比表

| 配置项 | Webhook模式 | WebSocket长连接模式 |
|--------|------------|-------------------|
| 环境变量 | `WECOM_TOKEN`, `WECOM_ENCODING_AES_KEY` | `WECOM_BOT_ID`, `WECOM_BOT_SECRET` |
| 模式开关 | 默认为Webhook模式 | `WECOM_STREAM_MODE=true` |
| 连接方式 | HTTP回调 | WebSocket长连接 |
| 公网需求 | 需要公网URL | 无需公网IP |
| 加解密 | 需要 | 无需 |
| 心跳维护 | 不需要 | 需要(30秒间隔) |
| 实时性 | 一般 | 好 |

## 企业微信管理后台配置差异

### Webhook模式
1. 在「应用管理」→「自建应用」创建应用
2. 在「接收消息」配置回调URL
3. 获取 `Token` 和 `EncodingAESKey`

### 长连接模式
1. 在「应用管理」→「智能机器人」创建机器人
2. 选择「API模式」→「长连接」
3. 获取 `BotID` 和 `Secret`

**注意**：`Secret` 不同于 `EncodingAESKey`，不能混用。

## 如何使用

### 启用长连接模式
1. 在 `.env` 文件中配置：
   ```bash
   WECOM_STREAM_MODE=true
   WECOM_BOT_ID=your_bot_id
   WECOM_BOT_SECRET=your_secret
   ```

2. 重启容器：
   ```bash
   docker-compose down && docker-compose up -d
   ```

### 切换回Webhook模式
1. 修改 `.env` 文件：
   ```bash
   WECOM_STREAM_MODE=false
   WECOM_TOKEN=your_token
   WECOM_ENCODING_AES_KEY=your_key
   ```

2. 重启容器

## 验证步骤

1. **查看启动日志**：
   ```bash
   docker-compose logs -f | grep -i "企业微信\|wecom"
   ```

2. **确认长连接配置同步**：
   - 日志应显示：`✅ 企业微信长连接配置已同步`
   - 日志应显示：`ℹ️ 企业微信长连接模式已启用`

3. **测试消息收发**：
   - 在企业微信中向机器人发送消息
   - 检查是否能正常接收和回复

## 回滚方案

如果长连接模式出现问题，快速回滚：
```bash
# 1. 修改.env为Webhook模式
WECOM_STREAM_MODE=false
WECOM_TOKEN=xxx
WECOM_ENCODING_AES_KEY=xxx

# 2. 重启服务
docker-compose down && docker-compose up -d
```

## 后续开发建议

当前修改为**配置框架层**，已实现：
- ✅ 环境变量配置支持
- ✅ 初始化脚本同步逻辑
- ✅ 依赖包安装
- ✅ 文档说明

**待实现**（需要修改 `@sunnoy/wecom` 插件源码）：
- WebSocket客户端实现
- 心跳机制
- 消息处理适配器
- 断线重连逻辑

建议先部署配置框架，然后分步骤实现插件层面的功能修改。

---

**GitHub操作建议**：
1. 将本分支推送到远程仓库
2. 创建Pull Request到 `main` 分支
3. 合并后构建新的Docker镜像
4. 部署测试环境验证功能

如需帮助，请参考详细文档：
- `WECOM-WEBSOCKET-UPGRADE.md` - 技术改造方案
- `WECOM-WEBSOCKET-GUIDE.md` - 用户使用指南