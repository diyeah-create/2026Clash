#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedup.py - 智能去重器（2026 优化）
✅ 基于核心指纹去重 | ✅ 保留参数最全节点 | ✅ 名称自动防冲突
✅ 不误删：同一服务器多配置视为不同节点
"""

import yaml
import hashlib
from collections import defaultdict

def generate_fingerprint(proxy: dict) -> str:
    """生成节点核心指纹（关键参数哈希）"""
    key_parts = [
        proxy.get("type", ""),
        proxy.get("server", ""),
        str(proxy.get("port", "")),
        proxy.get("uuid", proxy.get("password", "")),
        proxy.get("alterId", ""),
        proxy.get("cipher", ""),
        proxy.get("network", "tcp"),
        proxy.get("servername", proxy.get("sni", "")),
        proxy.get("flow", ""),
        str(proxy.get("reality-opts", {})),
        str(proxy.get("ws-opts", {})),
        str(proxy.get("grpc-opts", {})),
    ]
    raw = "|".join(str(p) for p in key_parts if p)
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def main():
    # 读取原始节点
    with open("proxies_raw.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    proxies = data.get("proxies", [])
    print(f"[INFO] 加载 {len(proxies)} 个原始节点")
    
    # 按指纹分组，保留参数最全的
    groups = defaultdict(list)
    for p in proxies:
        fp = generate_fingerprint(p)
        groups[fp].append(p)
    
    deduped = []
    name_count = defaultdict(int)
    for fp, items in groups.items():
        # 优先保留字段多的（参数更全）
        best = max(items, key=lambda x: len(x))
        # 名称防冲突
        name = best["name"]
        name_count[name] += 1
        if name_count[name] > 1:
            best["name"] = f"{name} #{name_count[name]}"
        deduped.append(best)
    
    # 输出
    output = {"proxies": deduped}
    with open("proxies.yaml", "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)
    
    print(f"[✅] 去重完成：{len(proxies)} → {len(deduped)} 个节点，保存至 proxies.yaml")

if __name__ == "__main__":
    main()
