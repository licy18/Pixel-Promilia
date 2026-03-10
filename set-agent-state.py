#!/usr/bin/env python3
"""Pixel Promilia - 设置任意访客 Agent 状态

使用方法：
    python3 set-agent-state.py [agent_id] [state] [detail]
    
示例：
    python3 set-agent-state.py coco idle "呱呱待命中"
    python3 set-agent-state.py gugu writing "咕咕正在写代码"
    python3 set-agent-state.py lumi researching "露米在查资料"
    python3 set-agent-state.py lumi error "露米遇到 Bug 了"
"""

import json
import sys
import os
from datetime import datetime

# 状态到区域的映射
AREA_MAP = {
    "idle": "breakroom",
    "writing": "writing",
    "researching": "writing",
    "executing": "writing",
    "syncing": "bedroom",
    "error": "error",
}

# 可用状态列表
VALID_STATES = set(AREA_MAP.keys())

# 脚本所在目录（Pixel-Promilia 根目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Agent 显示名称
AGENT_NAMES = {
    "coco": "呱呱",
    "gugu": "咕咕",
    "lumi": "露米",
}

def set_agent_state(agent_id: str, state: str, detail: str = None):
    """设置指定 Agent 的状态"""
    
    # 验证状态
    if state not in VALID_STATES:
        print(f"❌ 无效状态：{state}")
        print(f"   有效状态：{', '.join(VALID_STATES)}")
        return False
    
    # 读取当前状态（始终指向 Pixel-Promilia 目录）
    # 查找 Pixel-Promilia 目录
    # 脚本就在 Pixel-Promilia 目录，直接使用
    base_dir = SCRIPT_DIR
    agents_file = os.path.join(base_dir, "agents-state.json")
    if not os.path.exists(agents_file):
        print(f"❌ 文件不存在：{agents_file}")
        return False
    
    try:
        with open(agents_file, "r", encoding="utf-8") as f:
            agents = json.load(f)
    except Exception as e:
        print(f"❌ 读取失败：{e}")
        return False
    
    # 找到并更新 Agent
    found = False
    now = datetime.now().isoformat()
    for agent in agents:
        if agent.get("agentId") == agent_id:
            agent["state"] = state
            agent["area"] = AREA_MAP.get(state, "breakroom")
            agent["detail"] = detail or f"{AGENT_NAMES.get(agent_id, agent_id)} 状态：{state}"
            agent["updated_at"] = now
            agent["lastPushAt"] = now  # 关键：更新 lastPushAt 防止后端自动设为 offline
            agent["authStatus"] = "approved"  # 确保保持 approved 状态
            found = True
            break
    
    if not found:
        print(f"❌ 未找到 Agent：{agent_id}")
        print(f"   当前可用的 Agent:")
        for agent in agents:
            print(f"     - {agent['agentId']} ({agent['name']}) - 当前状态：{agent['state']}")
        return False
    
    # 保存状态
    try:
        with open(agents_file, "w", encoding="utf-8") as f:
            json.dump(agents, f, ensure_ascii=False, indent=2)
        
        agent_name = AGENT_NAMES.get(agent_id, agent_id)
        area = AREA_MAP.get(state, "breakroom")
        area_names = {
            "breakroom": "休息区",
            "writing": "工作区",
            "error": "Bug 区",
        }
        area_name = area_names.get(area, area)
        
        print(f"✅ 已更新 {agent_name} 的状态:")
        print(f"   状态：{state}")
        print(f"   区域：{area_name}")
        print(f"   详情：{detail or '无'}")
        print()
        print("📱 请刷新页面查看效果：Ctrl + Shift + R")
        return True
    except Exception as e:
        print(f"❌ 保存失败：{e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        print("当前可用的 Agent:")
        
        agents_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agents-state.json")
        if os.path.exists(agents_file):
            with open(agents_file, "r", encoding="utf-8") as f:
                agents = json.load(f)
            for agent in agents:
                current_state = agent.get('state', 'unknown')
                current_area = agent.get('area', 'unknown')
                print(f"  - {agent['agentId']:6} ({agent['name']}) - {current_state:12} → {current_area}")
        else:
            print("  (无可用 Agent，请先创建 agents-state.json)")
        
        print()
        print("有效状态:")
        for state, area in AREA_MAP.items():
            area_names = {
                "breakroom": "休息区",
                "writing": "工作区",
                "error": "Bug 区",
            }
            area_name = area_names.get(area, area)
            print(f"  - {state:12} → {area_name}")
        
        sys.exit(1)
    
    agent_id = sys.argv[1]
    state = sys.argv[2]
    detail = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = set_agent_state(agent_id, state, detail)
    sys.exit(0 if success else 1)
