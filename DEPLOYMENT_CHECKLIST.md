# Pixel Promilia 部署检查清单

**目的：** 确保每次修改后正确部署，避免服务中断

---

## 🔄 每次修改后的标准流程

### 1️⃣ 提交代码修改
```bash
cd /home/admin/.openclaw/workspace-coco/Pixel-Promilia
git add -A
git commit -m "描述修改内容"
```

### 2️⃣ 重启后端服务 ⚠️ **必须**
```bash
# 停止旧进程
pkill -f "python3.*app.py"

# 等待 2 秒
sleep 2

# 启动新进程
cd /home/admin/.openclaw/workspace-coco/Pixel-Promilia
nohup venv/bin/python3 backend/app.py > /tmp/pixel-promilia.log 2>&1 &

# 等待启动
sleep 3

# 检查服务状态
curl -s http://localhost:19000/health
```

### 3️⃣ 检查 Cloudflare Tunnel ⚠️ **必须**
```bash
# 检查 cloudflared 是否运行
ps aux | grep cloudflared | grep -v grep

# 如果未运行，启动它
nohup cloudflared tunnel --config ~/.cloudflared/0a31d825-8f9a-4456-b4af-e93e7b918426.yml run > /tmp/cloudflared.log 2>&1 &

# 等待连接
sleep 3

# 检查日志
tail -5 /tmp/cloudflared.log
# 应该看到 "Registered tunnel connection" 字样
```

### 4️⃣ 验证服务可用性
```bash
# 检查后端 API
curl -s http://localhost:19000/agents | python3 -m json.tool | head -10

# 检查 Agent 数量
curl -s http://localhost:19000/agents | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Agent 数量：{len(d)}')"

# 检查 Guest Agents 是否都在
curl -s http://localhost:19000/agents | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'  - {a[\"name\"]}: {a[\"state\"]} ({a[\"area\"]})') for a in d]"
```

### 5️⃣ 检查 agents-state.json
```bash
# 确认文件内容正确
cat /home/admin/.openclaw/workspace-coco/Pixel-Promilia/agents-state.json

# 如果 Agent 丢失，使用脚本恢复
python3 /home/admin/.openclaw/workspace-coco/set-agent-state.py coco idle "待命中"
python3 /home/admin/.openclaw/workspace-coco/set-agent-state.py gugu idle "待命中"
python3 /home/admin/.openclaw/workspace-coco/set-agent-state.py lumi idle "待命中"
```

### 6️⃣ 前端验证
- 浏览器访问：`https://office.pixel-promilia.xyz`
- **强制刷新：** Ctrl + Shift + R（清除缓存）
- 检查控制台：F12 → Console（查看是否有 JS 错误）
- 确认 3 个 Agent 都显示在正确位置

---

## 🚨 常见问题排查

### 问题 1：Agent 消失
**症状：** 页面只显示 Star，没有呱呱/咕咕/露米

**解决：**
```bash
# 检查 agents-state.json
cat /home/admin/.openclaw/workspace-coco/Pixel-Promilia/agents-state.json

# 如果只有 Star，手动恢复
python3 /home/admin/.openclaw/workspace-coco/set-agent-state.py coco idle "待命中"
python3 /home/admin/.openclaw/workspace-coco/set-agent-state.py gugu idle "待命中"
python3 /home/admin/.openclaw/workspace-coco/set-agent-state.py lumi idle "待命中"

# 重启后端
pkill -f "python3.*app.py"
sleep 2
cd /home/admin/.openclaw/workspace-coco/Pixel-Promilia && nohup venv/bin/python3 backend/app.py > /tmp/pixel-promilia.log 2>&1 &
```

### 问题 2：Cloudflare Tunnel 错误 1033
**症状：** 访问页面显示 Cloudflare Tunnel error

**解决：**
```bash
# 检查 cloudflared 进程
ps aux | grep cloudflared | grep -v grep

# 如果未运行，启动
nohup cloudflared tunnel --config ~/.cloudflared/0a31d825-8f9a-4456-b4af-e93e7b918426.yml run > /tmp/cloudflared.log 2>&1 &

# 检查连接
sleep 3
tail -10 /tmp/cloudflared.log
# 应该看到 "Registered tunnel connection"
```

### 问题 3：后端无法启动
**症状：** `curl http://localhost:19000/health` 无响应

**解决：**
```bash
# 检查端口占用
lsof -i :19000

# 杀掉占用进程
pkill -f "python3.*app.py"

# 检查日志
tail -30 /tmp/pixel-promilia.log

# 重新启动
cd /home/admin/.openclaw/workspace-coco/Pixel-Promilia
venv/bin/python3 backend/app.py
```

---

## 📋 快速检查脚本

创建 `check-deployment.sh`：

```bash
#!/bin/bash
echo "🔍 检查后端服务..."
curl -s http://localhost:19000/health && echo "✅ 后端正常" || echo "❌ 后端异常"

echo -e "\n🔍 检查 Agent 数量..."
AGENT_COUNT=$(curl -s http://localhost:19000/agents | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$AGENT_COUNT" = "3" ]; then
    echo "✅ Agent 数量：$AGENT_COUNT"
else
    echo "❌ Agent 数量：$AGENT_COUNT (期望 3)"
fi

echo -e "\n🔍 检查 Cloudflare Tunnel..."
if ps aux | grep cloudflared | grep -v grep > /dev/null; then
    echo "✅ cloudflared 运行中"
else
    echo "❌ cloudflared 未运行"
fi

echo -e "\n🔍 检查 agents-state.json..."
if [ -f "agents-state.json" ]; then
    FILE_COUNT=$(cat agents-state.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
    echo "✅ 文件存在，Agent 数量：$FILE_COUNT"
else
    echo "❌ 文件不存在"
fi
```

使用：
```bash
chmod +x check-deployment.sh
./check-deployment.sh
```

---

## ✅ 完成标志

- [ ] 后端服务运行（`/health` 返回 ok）
- [ ] 3 个 Guest Agents 都在（呱呱/咕咕/露米）
- [ ] Cloudflare Tunnel 已连接（日志显示 "Registered tunnel connection"）
- [ ] 页面可访问（https://office.pixel-promilia.xyz）
- [ ] 前端显示 3 个 Agent 在正确位置

---

**最后更新：** 2026-03-10  
**教训来源：** 忘记重启后端和检查 Tunnel 导致服务中断
