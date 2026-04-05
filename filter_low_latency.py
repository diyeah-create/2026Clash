import yaml
import os

if os.path.exists('proxies_tested.yaml'):
    with open('proxies_tested.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
else:
    print("⚠️ proxies_tested.yaml 不存在，使用 proxies_dedup.yaml 作为 fallback")
    with open('proxies_dedup.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

proxies = data.get('proxies', [])

MAX_LATENCY_MS = 8000
filtered = [p for p in proxies if isinstance(p.get('latency'), (int, float)) and p.get('latency') <= MAX_LATENCY_MS]

print(f"第一阶段 fast 测速完成 → 低延迟节点: {len(filtered)} / {len(proxies)}（阈值 {MAX_LATENCY_MS}ms）")

with open('low_latency.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': filtered}, f, allow_unicode=True, sort_keys=False)

print("✅ low_latency.yaml 已生成，准备第二阶段下载测速")
