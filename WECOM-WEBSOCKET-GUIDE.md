# 企业微信智能机器人长连接（WebSocket）使用指南

## 概述

本指南介绍如何使用企业微信智能机器人的长连接（WebSocket）模式，相比传统的HTTP Webhook模式，长连接模式具有以下优势：

- **无需公网IP**：适合内网环境部署
- **低延迟**：消息实时性更好
- **简化开发**：无需处理消息加解密
- **流式消息**：支持流式消息推送

## 配置步骤

### 1. 企业微信管理后台配置

#### 1.1 创建智能机器人
1. 登录企业微信管理后台
2. 进入「应用管理」→「智能机器人」
3. 点击「创建机器人」
4. 设置机器人名称、头像等基本信息

#### 1.2 配置API模式
1. 在机器人配置页面，选择「API模式」
2. 选择「长连接」方式
3. 获取以下凭证：
   - **BotID**：智能机器人的唯一标识
   - **Secret**：长连接专用密钥（注意：不同于Webhook的EncodingAESKey）

#### 1.3 重要区别
| 凭证类型 | Webhook模式 | WebSocket长连接模式 |
|---------|------------|-------------------|
| 身份验证 | Token + EncodingAESKey | BotID + Secret |
| 获取位置 | 回调配置页面 | 智能机器人API模式页面 |
| 用途 | HTTP回调加解密 | WebSocket连接身份验证 |

### 2. Docker环境配置

#### 2.1 基础配置
在`.env`文件中添加以下配置：

```bash
# 启用长连接模式
WECOM_STREAM_MODE=true

# 长连接凭证（从企业微信管理后台获取）
WECOM_BOT_ID=bot_xxxxxx
WECOM_BOT_SECRET=secret_xxxxxx

# 可选：高级配置
WECOM_WS_URL=wss://openws.work.weixin.qq.com  # WebSocket地址（默认官方地址）
WECOM_HEARTBEAT_INTERVAL=30000                 # 心跳间隔（毫秒，默认30秒）
WECOM_RECONNECT_RETRIES=5                      # 断线重连次数（默认5次）

# 通用配置（与Webhook模式相同）
WECOM_DM_POLICY=open                          # 私聊策略：open/closed/friend-only
WECOM_ALLOW_FROM=*                            # 允许来源
WECOM_GROUP_POLICY=open                       # 群组策略
```

#### 2.2 模式切换
- **切换到长连接模式**：设置`WECOM_STREAM_MODE=true`并配置`WECOM_BOT_ID`和`WECOM_BOT_SECRET`
- **切换回Webhook模式**：设置`WECOM_STREAM_MODE=false`并配置`WECOM_TOKEN`和`WECOM_ENCODING_AES_KEY`
- **双模式不兼容**：不能同时使用两种模式，系统会根据`WECOM_STREAM_MODE`自动选择

### 3. 启动服务

#### 3.1 启动容器
```bash
# 使用docker-compose启动
docker-compose up -d

# 查看日志确认连接状态
docker-compose logs -f
```

#### 3.2 验证连接
成功启动后，查看日志中应包含以下信息：
```
✅ 企业微信长连接配置已同步
ℹ️ 企业微信长连接模式已启用
WebSocket连接已建立
心跳发送成功
```

### 4. 功能特性

#### 4.1 消息类型支持
长连接模式支持以下消息类型：
- 文本消息
- 图片消息（仅单聊）
- 图文混排消息
- 语音消息（转为文本，仅单聊）
- 文件消息（仅单聊）

#### 4.2 流式消息
支持流式消息回复机制：
```javascript
// 首次回复
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msgtype": "stream",
    "stream": {
      "id": "stream_123",
      "finish": false,
      "content": "正在为您查询..."
    }
  }
}

// 更新流式消息
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msgtype": "stream",
    "stream": {
      "id": "stream_123",  // 相同的stream.id
      "finish": false,
      "content": "正在为您查询...已找到10条结果"
    }
  }
}

// 完成流式消息
{
  "cmd": "aibot_respond_msg",
  "body": {
    "msgtype": "stream",
    "stream": {
      "id": "stream_123",
      "finish": true,      // 设置为true表示完成
      "content": "查询完成！"
    }
  }
}
```

#### 4.3 主动推送
支持在没有用户消息触发的情况下主动推送消息：
- 定时提醒（日报、周报等）
- 异步任务通知
- 系统告警推送
- 业务状态更新

### 5. 监控与排错

#### 5.1 连接状态监控
- **正常状态**：`connectionStatus: 'connected'`
- **心跳状态**：每30秒发送一次ping，检查响应
- **消息统计**：统计消息收发数量和时间

#### 5.2 常见问题

##### 问题1：连接建立失败
**可能原因**：
- BotID或Secret错误
- 网络无法访问`wss://openws.work.weixin.qq.com`
- 企业微信管理后台未启用长连接模式

**解决方案**：
1. 检查企业微信管理后台的BotID和Secret
2. 测试网络连通性：`curl -I https://openws.work.weixin.qq.com`
3. 确认已选择「长连接」API模式

##### 问题2：心跳超时
**可能原因**：
- 网络不稳定
- 服务端连接中断
- 防火墙限制

**解决方案**：
1. 检查网络连接
2. 调整心跳间隔：`WECOM_HEARTBEAT_INTERVAL=60000`（60秒）
3. 增加重连次数：`WECOM_RECONNECT_RETRIES=10`

##### 问题3：消息无法接收
**可能原因**：
- 连接已断开
- 订阅请求失败
- 企业微信配置错误

**解决方案**：
1. 查看日志确认连接状态
2. 检查订阅请求是否成功
3. 验证企业微信机器人是否在线

#### 5.3 日志分析
关键日志信息：
```log
# 连接成功
[INFO] WeComStreamService - WebSocket连接已建立
[INFO] WeComStreamService - 订阅请求成功

# 心跳正常
[DEBUG] WeComStreamService - 心跳发送成功
[DEBUG] WeComStreamService - 心跳响应正常

# 消息处理
[INFO] WeComStreamService - 收到消息: msgid=msg_123, type=text
[INFO] WeComStreamService - 回复消息成功: req_id=req_456

# 连接问题
[WARN] WeComStreamService - 心跳超时，准备重连
[ERROR] WeComStreamService - 连接断开，开始重连 (尝试1/5)
```

### 6. 性能优化

#### 6.1 连接池管理
- 保持单一连接（企业微信限制每个机器人只能有一个连接）
- 实现连接复用
- 优化心跳机制减少资源消耗

#### 6.2 消息队列
- 实现消息队列缓存
- 支持消息重发机制
- 控制消息发送频率（企业微信限制：30条/分钟，1000条/小时）

#### 6.3 资源监控
```bash
# 监控内存使用
docker stats openclaw-docker-cn-im

# 查看连接状态
docker exec openclaw-docker-cn-im curl http://localhost:18789/status
```

### 7. 安全考虑

#### 7.1 凭证安全
- **BotID和Secret**：等同于密码，需妥善保管
- **环境变量**：使用`.env`文件管理，不要提交到代码仓库
- **访问控制**：配置`WECOM_ALLOW_FROM`限制消息来源

#### 7.2 网络安全
- **WebSocket**：使用`wss://`加密连接
- **内网部署**：长连接模式特别适合内网环境
- **防火墙**：确保能访问企业微信服务器

#### 7.3 数据安全
- **消息内容**：企业微信已对消息内容加密
- **本地存储**：不存储敏感消息内容
- **日志脱敏**：日志中不记录完整消息内容

### 8. 回滚方案

#### 8.1 快速回滚到Webhook模式
```bash
# 修改.env文件
WECOM_STREAM_MODE=false
WECOM_TOKEN=your_token
WECOM_ENCODING_AES_KEY=your_key

# 重启服务
docker-compose down && docker-compose up -d
```

#### 8.2 版本回退
```bash
# 切换到稳定版本
git checkout v1.2.0
docker-compose build
docker-compose up -d
```

### 9. 最佳实践

#### 9.1 开发环境
- 使用测试用的BotID和Secret
- 配置完整的日志级别
- 实现自动化测试

#### 9.2 生产环境
- 使用正式的BotID和Secret
- 配置适当的监控告警
- 定期检查连接状态
- 备份配置文件

#### 9.3 性能调优
- 根据业务量调整心跳间隔
- 配置合理的重连策略
- 监控消息队列长度
- 优化消息处理逻辑

### 10. 参考资料

1. **企业微信官方文档**：
   - [智能机器人长连接](https://developer.work.weixin.qq.com/document/path/101463)
   - [消息格式说明](https://developer.work.weixin.qq.com/document/path/90239)
   - [API错误码](https://developer.work.weixin.qq.com/document/path/90313)

2. **相关工具**：
   - [企业微信Node.js SDK](https://www.npmjs.com/package/@wecom/aibot-node-sdk)
   - [WebSocket客户端](https://www.npmjs.com/package/ws)

3. **社区资源**：
   - [OpenClaw官方文档](https://docs.openclaw.ai)
   - [GitHub Issues](https://github.com/justlovemaki/openclaw-docker-cn-im/issues)

---

**最后更新**：2026-03-10  
**适用版本**：openclaw-docker-cn-im >= 2026.3.10  
**维护者**：jokerxliu  

如有问题，请提交 [GitHub Issue](https://github.com/Joker2016/openclaw-docker-cn-im/issues) 或联系维护者。