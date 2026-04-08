import yaml
import os
import time

start = time.time()

# 读取合并后的文件
if os.path.exists('proxies_tested.yaml'):
    with open('proxies_tested.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
else:
    print("⚠️ proxies_tested.yaml 不存在，使用 proxies_dedup.yaml")
    with open('proxies_dedup.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

proxies = data.get('proxies', [])

# 更鲁棒的延迟提取（支持 int、float、str）
def get_latency(p):
    lat = p.get('latency') or p.get('ping') or 0
    if isinstance(lat, str):
        try:
            lat = float(lat.replace('ms', '').strip())
        except:
            lat = 0
    return float(lat) if isinstance(lat, (int, float)) else 0

MAX_LATENCY_MS = 5000
filtered = [p for p in proxies if get_latency(p) <= MAX_LATENCY_MS]

print(f"第一阶段合并后 → 低延迟节点 (<{MAX_LATENCY_MS}ms): {len(filtered)} / {len(proxies)}")

# 调试输出前 5 个节点的延迟（方便你确认）
if proxies:
    print("前 5 个节点延迟示例：")
    for p in proxies[:5]:
        print(f"  {p.get('name', '未知')} → {get_latency(p)}ms")

if len(filtered) == 0:
    print("⚠️ 没有 <5000ms 节点，使用全部节点作为 fallback")
    filtered = proxies

with open('low_latency.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': filtered}, f, allow_unicode=True, sort_keys=False)

print(f"✅ low_latency.yaml 生成完成（{len(filtered)} 个节点）")
print(f"过滤耗时: {time.time() - start:.1f} 秒")
