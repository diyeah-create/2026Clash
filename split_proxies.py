#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
split_proxies.py - 节点分片脚本（2026 优化）
✅ 将节点均匀拆分为 8 个分片，支持并行测速
"""

import yaml
import math

def main():
    # 加载去重后的节点
    with open("proxies.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    proxies = data.get("proxies", [])
    
    if not proxies:
        print("[WARN] 无节点可分片", file=sys.stderr)
        return
    
    # 拆分为 8 个分片
    chunk_size = math.ceil(len(proxies) / 8)
    print(f"总节点: {len(proxies)} → 拆分成 8 个分片并行测速")
    
    for i in range(8):
        start = i * chunk_size
        end = start + chunk_size
        chunk = proxies[start:end]
        if not chunk:
            continue
        
        output = {"proxies": chunk}
        output_file = f"proxies_chunk_{i}.yaml"
        with open(output_file, "w", encoding="utf-8") as f:
            yaml.dump(output, f, allow_unicode=True, sort_keys=False)
        
        print(f"  分片 {i+1}/8：{len(chunk)} 个节点 → {output_file}")
    
    print("[✅] 分片完成")

if __name__ == "__main__":
    main()
