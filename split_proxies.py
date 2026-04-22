import yaml
import sys
import math
import json

# ==================== 动态微小 chunk 配置 ====================
CHUNK_SIZE = 10          # 严格每 10 个节点 1 个 chunk（你要求的动态数量）
# =========================================================

with open('proxies_dedup.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

total_chunks = math.ceil(len(proxies) / CHUNK_SIZE)
print(f"总节点: {len(proxies)} → 拆分成 {total_chunks} 个微小 chunk（每 chunk 严格 {CHUNK_SIZE} 个节点）")

chunk_files = []
for i in range(total_chunks):
    start = i * CHUNK_SIZE
    end = min(start + CHUNK_SIZE, len(proxies))
    chunk = proxies[start:end]
    
    # 文件名补零（0000、0001...）方便排序
    chunk_file = f"proxies_chunk_{i:04d}.yaml"
    with open(chunk_file, 'w', encoding='utf-8') as f:
        yaml.dump({'proxies': chunk}, f, allow_unicode=True, sort_keys=False)
    
    chunk_files.append(chunk_file)
    print(f"  chunk {i+1:04d}/{total_chunks:04d}：{len(chunk)} 个节点 → {chunk_file}")

# 输出 chunks.json 供 workflow 动态 matrix 使用（队列调度核心）
with open('chunks.json', 'w', encoding='utf-8') as f:
    json.dump(chunk_files, f)

print(f"✅ 每 10 个节点 1 个 chunk 拆分完成！共 {len(chunk_files)} 个 chunk，已生成 chunks.json")
