import yaml

# 读取 fast 模式测速结果
with open('proxies_tested.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

# 过滤低延迟节点（可自行修改阈值）
MAX_LATENCY_MS = 8000
filtered = [p for p in proxies if isinstance(p.get('latency'), (int, float)) and p.get('latency') <= MAX_LATENCY_MS]

print(f"第一阶段 fast 测速完成 → 低延迟节点: {len(filtered)} / {len(proxies)}（阈值 {MAX_LATENCY_MS}ms）")

# 写入临时文件给第二阶段 download 测速
with open('low_latency.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': filtered}, f, allow_unicode=True, sort_keys=False)

print("✅ low_latency.yaml 已生成，准备第二阶段下载测速")
