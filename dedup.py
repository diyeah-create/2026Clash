import yaml
import hashlib

with open('raw_proxies.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

print(f"原始节点数量: {len(proxies)}")

# 更严格去重：以核心参数哈希为键（忽略 name）
def get_proxy_key(p):
    core = {
        'type': p.get('type'),
        'server': p.get('server'),
        'port': p.get('port'),
        'uuid': p.get('uuid') or p.get('password') or p.get('cipher'),
        'cipher': p.get('cipher')
    }
    return hashlib.md5(str(core).encode()).hexdigest()

seen = {}
deduped = []
for p in proxies:
    key = get_proxy_key(p)
    if key not in seen:
        seen[key] = True
        deduped.append(p)

print(f"严格去重后: {len(deduped)} 个节点")

# 强制所有 name 唯一（防止任何重复）
name_count = {}
final_proxies = []
for p in deduped:
    original_name = p.get('name', f"节点-{len(final_proxies)}")
    if original_name in name_count:
        name_count[original_name] += 1
        new_name = f"{original_name} #{name_count[original_name]}"
        p['name'] = new_name
    else:
        name_count[original_name] = 1
    final_proxies.append(p)

with open('proxies_dedup.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': final_proxies}, f, allow_unicode=True, sort_keys=False)

print(f"✅ 最终去重 + 强制唯一名称完成！共 {len(final_proxies)} 个节点 → proxies_dedup.yaml")
