#!/bin/bash
# Pixel Promilia - 露米状态切换脚本

STATE=$1
DETAIL=$2

if [ -z "$STATE" ]; then
    echo "用法：./set-lumi-state.sh [状态] [详情]"
    echo ""
    echo "可用状态:"
    echo "  idle       - 休息区待命"
    echo "  writing    - 工作区工作"
    echo "  researching - 工作区调研"
    echo "  executing  - 工作区执行"
    echo "  error      - Bug 区报错"
    echo ""
    echo "示例:"
    echo "  ./set-lumi-state.sh idle '露米在休息'"
    echo "  ./set-lumi-state.sh writing '露米正在写代码'"
    exit 1
fi

python3 << PYEOF
import json
from datetime import datetime

state = "$STATE"
detail = "$DETAIL" or f"露米状态：$state"

# 状态到区域的映射
area_map = {
    "idle": "breakroom",
    "writing": "writing",
    "researching": "writing",
    "executing": "writing",
    "syncing": "writing",
    "error": "error"
}

area = area_map.get(state, "breakroom")

with open('agents-state.json', 'r') as f:
    agents = json.load(f)

for agent in agents:
    if agent['agentId'] == 'lumi':
        agent['state'] = state
        agent['detail'] = detail
        agent['area'] = area
        agent['updated_at'] = datetime.now().isoformat()
        break

with open('agents-state.json', 'w') as f:
    json.dump(agents, f, ensure_ascii=False, indent=2)

print(f"✅ 露米状态已修改：{state}")
print(f"   区域：{area}")
print(f"   详情：{detail}")
print("")
print("📱 请刷新页面查看效果：Ctrl + Shift + R")
PYEOF
