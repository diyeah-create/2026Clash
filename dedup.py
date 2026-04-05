import yaml
import hashlib

with open('raw_proxies.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

print(f"原始节点数量: {len(proxies)}")

# 终极去重：核心参数哈希（完全忽略 name）
def get_proxy_key(p):
    core = {
        'type': p.get('type'),
        'server': p.get('server'),
        'port': p.get('port'),
        'uuid': p.get('uuid') or p.get('password'),
        'cipher': p.get('cipher'),
        'password': p.get('password')
    }
    return hashlib.md5(str(sorted(core.items())).encode()).hexdigest()

seen = {}
deduped = []
for p in proxies:
    key = get_proxy_key(p)
    if key not in seen:
        seen[key] = True
        deduped.append(p)

print(f"哈希严格去重后: {len(deduped)} 个节点")

# 强制全局唯一名称（彻底消灭 duplicate name）
final_proxies = []
name_set = set()
for i, p in enumerate(deduped):
    original_name = p.get('name', f"节点-{i}")
    base_name = original_name
    counter = 1
    while base_name in name_set:
        base_name = f"{original_name} #{counter}"
        counter += 1
    p['name'] = base_name
    name_set.add(base_name)
    final_proxies.append(p)

with open('proxies_dedup.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': final_proxies}, f, allow_unicode=True, sort_keys=False)

print(f"✅ 终极去重 + 强制唯一名称完成！共 {len(final_proxies)} 个节点 → proxies_dedup.yaml")
