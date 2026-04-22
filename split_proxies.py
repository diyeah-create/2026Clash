import yaml
import sys
import math

SHARDS = 12   # ← 这里改成你想要的数量（推荐 8，最大建议 10）

with open('proxies_dedup.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

print(f"总节点: {len(proxies)} → 拆分成 {SHARDS} 个分片并行测速")

chunk_size = math.ceil(len(proxies) / SHARDS)
for i in range(SHARDS):
    start = i * chunk_size
    end = min(start + chunk_size, len(proxies))
    chunk = proxies[start:end]
    
    with open(f'proxies_chunk_{i}.yaml', 'w', encoding='utf-8') as f:
        yaml.dump({'proxies': chunk}, f, allow_unicode=True, sort_keys=False)
    
    print(f"  分片 {i+1}/{SHARDS}：{len(chunk)} 个节点 → proxies_chunk_{i}.yaml")
