#!/usr/bin/env python3
"""Guest Agents 恢复脚本 - 在 backend/app.py 启动前运行"""

import json
import os
import sys
from datetime import datetime

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
agents_file = os.path.join(root_dir, "agents-state.json")
default_guest_file = os.path.join(root_dir, "guest-agents.default.json")

def restore_guest_agents():
    """如果 guest agents 丢失，从默认配置恢复"""
    
    # 读取当前 agents
    if not os.path.exists(agents_file):
        print(f"⚠️ {agents_file} 不存在，跳过恢复")
        return
    
    try:
        with open(agents_file, "r", encoding="utf-8") as f:
            agents = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取 agents-state.json 失败：{e}")
        return
    
    # 检查 guest agents 数量
    guest_agents = [a for a in agents if not a.get("isMain")]
    
    if len(guest_agents) >= 3:
        print(f"✅ Guest agents 数量正常：{len(guest_agents)}")
        return
    
    print(f"🔧 Guest agents 不足 ({len(guest_agents)}/3)，开始恢复...")
    
    # 读取默认配置
    if not os.path.exists(default_guest_file):
        print(f"⚠️ 默认配置文件不存在：{default_guest_file}")
        return
    
    try:
        with open(default_guest_file, "r", encoding="utf-8") as f:
            default_guests = json.load(f)
    except Exception as e:
        print(f"⚠️ 读取默认配置失败：{e}")
        return
    
    # 保留 main agent
    main_agent = next((a for a in agents if a.get("isMain")), None)
    now = datetime.now().isoformat()
    
    # 更新 guest agents 的时间戳
    for g in default_guests:
        g["updated_at"] = now
        g["lastPushAt"] = now
    
    # 合并
    restored = [main_agent] + default_guests if main_agent else default_guests
    
    # 保存
    try:
        with open(agents_file, "w", encoding="utf-8") as f:
            json.dump(restored, f, ensure_ascii=False, indent=2)
        print(f"🔧 已恢复 guest agents: {[g['name'] for g in default_guests]}")
    except Exception as e:
        print(f"⚠️ 保存失败：{e}")

if __name__ == "__main__":
    restore_guest_agents()
