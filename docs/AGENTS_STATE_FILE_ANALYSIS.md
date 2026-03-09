# agents-state.json 修改点全面分析

**分析日期：** 2026-03-10  
**分析目的：** 找出所有可能修改 `agents-state.json` 的代码位置，排查 Agent 消失的根因

---

## 📍 文件位置

- **路径：** `/home/admin/.openclaw/workspace-coco/Pixel-Promilia/agents-state.json`
- **后端定义：** `backend/app.py` 第 43 行
  ```python
  AGENTS_STATE_FILE = os.path.join(ROOT_DIR, "agents-state.json")
  ```

---

## 🔍 所有修改点（共 9 处）

### ✅ 1. 初始化检查（第 800 行）
**位置：** `backend/app.py` 启动时  
**代码：**
```python
# Ensure files exist
if not os.path.exists(AGENTS_STATE_FILE):
    save_agents_state(DEFAULT_AGENTS)
```
**触发条件：** 文件不存在时  
**修改内容：** 写入默认的 `DEFAULT_AGENTS`（只有 Star）  
**风险等级：** 🔴 **高** - 如果文件被意外删除，会重置为只有 Star

---

### ⚠️ 2. `/agents` 接口清理（第 867 行）
**位置：** `get_agents()` 函数  
**代码：**
```python
for a in agents:
    # ... 检查 authStatus, lastPushAt ...
    cleaned_agents.append(a)

save_agents_state(cleaned_agents)  # 第 867 行
```
**触发条件：** 每次前端轮询 `/agents` 接口（约每秒 1 次）  
**修改内容：**
- 检查 `authStatus == "pending"` 且超时 → 删除 Agent
- 检查 `authStatus == "approved"` 且 5 分钟无推送 → 设为 `offline`
**风险等级：** 🟡 **中** - 会修改 `authStatus`，但不会删除 guest agents

---

### ✅ 3. `/agent-approve` 批准接口（第 891 行）
**位置：** `agent_approve()` 函数  
**代码：**
```python
target["authStatus"] = "approved"
target["authApprovedAt"] = datetime.now().isoformat()
target["authExpiresAt"] = (datetime.now() + timedelta(hours=24)).isoformat()
save_agents_state(agents)  # 第 891 行
```
**触发条件：** 手动批准 Agent 加入  
**修改内容：** 更新 `authStatus`, `authApprovedAt`, `authExpiresAt`  
**风险等级：** 🟢 **低** - 只修改批准相关字段

---

### 🔴 4. `/agent-reject` 拒绝接口（第 928 行）
**位置：** `agent_reject()` 函数  
**代码：**
```python
target["authStatus"] = "rejected"
target["authRejectedAt"] = datetime.now().isoformat()

# Remove from agents list
agents = [a for a in agents if a.get("agentId") != agent_id or a.get("isMain")]
save_agents_state(agents)  # 第 928 行
```
**触发条件：** 手动拒绝 Agent  
**修改内容：** **删除 guest agent**（只保留 main agent）  
**风险等级：** 🔴 **高** - 直接删除 Agent

---

### ⚠️ 5. `/join-agent` 加入接口 - 并发检查（第 1024 行）
**位置：** `join_agent()` 函数  
**代码：**
```python
if active_count >= max_concurrent:
    save_agents_state(agents)  # 第 1024 行
    return jsonify({"ok": False, "msg": "并发已达上限"})
```
**触发条件：** 新 Agent 加入时检查并发限制  
**修改内容：** 可能触发清理逻辑  
**风险等级：** 🟡 **中**

---

### ✅ 6. `/join-agent` 加入接口 - 保存新 Agent（第 1072 行）
**位置：** `join_agent()` 函数  
**代码：**
```python
agents.append({
    "agentId": agent_id,
    "name": name,
    # ... 新 Agent 数据 ...
})
save_agents_state(agents)  # 第 1072 行
```
**触发条件：** 新 Agent 成功加入  
**修改内容：** 添加新 Agent  
**风险等级：** 🟢 **低** - 添加而非删除

---

### 🔴 7. `/leave-agent` 离开接口（第 1121 行）
**位置：** `leave_agent()` 函数  
**代码：**
```python
new_agents = [a for a in agents if a.get("isMain") or a.get("agentId") != target.get("agentId")]
save_agents_state(new_agents)  # 第 1121 行
```
**触发条件：** Agent 主动离开  
**修改内容：** **删除 guest agent**  
**风险等级：** 🔴 **高** - 直接删除 Agent

---

### ✅ 8. `/agent-push` 推送状态接口（第 1207 行）
**位置：** `agent_push()` 函数  
**代码：**
```python
target["state"] = state
target["detail"] = detail
target["updated_at"] = datetime.now().isoformat()
target["lastPushAt"] = datetime.now().isoformat()
save_agents_state(agents)  # 第 1207 行
```
**触发条件：** Agent 推送状态更新  
**修改内容：** 更新状态字段  
**风险等级：** 🟢 **低** - 正常更新

---

### ✅ 9. 恢复机制（第 2120 行）
**位置：** `restore_guest_agents_if_needed()` 函数  
**代码：**
```python
if len(guest_agents) < 3:
    # 从 guest-agents.default.json 恢复
    restored = [main_agent] + default_guests
    save_agents_state(restored)  # 第 2120 行
```
**触发条件：** 后端启动时检查  
**修改内容：** 恢复丢失的 guest agents  
**风险等级：** 🟢 **低** - 恢复而非破坏

---

## 📊 风险分析总结

### 🔴 高风险（会删除 Agent）
| 行号 | 接口 | 说明 |
|------|------|------|
| 800 | 启动初始化 | 文件不存在时重置为默认值 |
| 928 | `/agent-reject` | 拒绝后删除 Agent |
| 1121 | `/leave-agent` | 离开后删除 Agent |

### 🟡 中风险（会修改状态）
| 行号 | 接口 | 说明 |
|------|------|------|
| 867 | `/agents` | 轮询时检查并可能设为 offline |
| 1024 | `/join-agent` | 并发检查时保存 |

### 🟢 低风险（正常操作）
| 行号 | 接口 | 说明 |
|------|------|------|
| 891 | `/agent-approve` | 批准操作 |
| 1072 | `/join-agent` | 添加新 Agent |
| 1207 | `/agent-push` | 状态更新 |
| 2120 | 恢复机制 | 自动恢复 |

---

## 🐛 可能的根因

### 根因 1：文件被意外删除
**场景：** 手动清理、脚本误操作、磁盘问题  
**结果：** 触发第 800 行初始化逻辑，重置为只有 Star  
**证据：** 多次发现 `agents-state.json` 只有 Star

### 根因 2：/agents 接口的清理逻辑
**场景：** 前端轮询时触发清理  
**问题：** 虽然已改为 24 小时超时，但代码中仍有旧注释  
**代码：** 第 860 行
```python
if age > 86400:  # 5 分钟无推送自动离线 ← 注释还是旧的
```

### 根因 3：其他进程修改
**可能：**
- 其他脚本直接写入文件
- 编辑器自动保存
- 同步工具冲突

---

## ✅ 已实施的防护措施

### 1. 默认配置备份
**文件：** `guest-agents.default.json`  
**作用：** 存储 3 个 guest agents 的默认配置

### 2. 自动恢复脚本
**文件：** `scripts/restore-guest-agents.py`  
**触发：** 后端启动时自动运行  
**逻辑：** 检查 guest agents 数量，不足时恢复

### 3. 超时时间延长
**修改：** 5 分钟 → 24 小时（86400 秒）  
**位置：** 第 860 行、第 1003 行

---

## 📋 建议改进

### 1. 修复注释
```python
# 修改前
if age > 86400:  # 5 分钟无推送自动离线

# 修改后
if age > 86400:  # 24 小时无推送自动离线
```

### 2. 添加文件保护
在 `store_utils.py` 中添加保护逻辑：
```python
def save_agents_state(path: str, agents: list):
    """Persist agents list to path."""
    # 保护：不允许保存只有 main agent 的状态（除非是初始化）
    guest_count = sum(1 for a in agents if not a.get("isMain"))
    if guest_count < 3 and os.path.exists(path):
        print(f"⚠️ 警告：尝试保存 {guest_count} 个 guest agents，已阻止")
        return  # 阻止保存
    _save_json(path, agents)
```

### 3. 添加版本控制
每次保存时记录版本号，便于追踪修改历史：
```python
{
    "version": 2,
    "last_modified": "2026-03-10T05:00:00",
    "modified_by": "restore-guest-agents.py",
    "agents": [...]
}
```

### 4. 添加监控日志
在关键修改点添加日志：
```python
print(f"📝 save_agents_state: {len(agents)} agents, guests: {guest_count}")
```

---

## 🔧 外部修改点（非 backend/app.py）

### 1. `set-agent-state.py`
**用途：** 手动设置 Agent 状态  
**修改内容：** 更新 `state`, `area`, `detail`, `updated_at`, `lastPushAt`, `authStatus`  
**风险：** 🟢 低 - 只更新字段，不删除 Agent

### 2. `scripts/restore-guest-agents.py`
**用途：** 自动恢复 guest agents  
**修改内容：** 从默认配置恢复  
**风险：** 🟢 低 - 恢复操作

---

## 📝 结论

**最可能的根因：** `agents-state.json` 文件被意外删除或覆盖，触发第 800 行的初始化逻辑，重置为只有 Star。

**已实施的防护：**
1. ✅ 添加 `guest-agents.default.json` 备份
2. ✅ 添加自动恢复脚本
3. ✅ 后端启动时自动检查并恢复

**建议继续改进：**
1. 修复过时的注释
2. 添加保存保护逻辑
3. 添加版本控制和监控日志

---

**分析者：** 呱呱 🐸  
**分析时间：** 2026-03-10 05:07
