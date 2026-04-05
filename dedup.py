import yaml

with open('raw_proxies.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

print(f"原始节点数量: {len(proxies)}")

# 严格去重（以 name + server + port 为唯一键）
seen = {}
deduped = []
for p in proxies:
    key = (p.get('name'), p.get('server'), p.get('port'))
    if key not in seen:
        seen[key] = True
        deduped.append(p)

print(f"基础去重后: {len(deduped)} 个节点")

# 防重名（自动加序号）
name_count = {}
final_proxies = []
for p in deduped:
    original_name = p.get('name', '未知节点')
    if original_name in name_count:
        name_count[original_name] += 1
        new_name = f"{original_name} #{name_count[original_name]}"
        p['name'] = new_name
    else:
        name_count[original_name] = 1
    final_proxies.append(p)

with open('proxies_dedup.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': final_proxies}, f, allow_unicode=True, sort_keys=False)

print(f"✅ 最终去重 + 防重名完成！共 {len(final_proxies)} 个节点（已保留全部）→ proxies_dedup.yaml")
