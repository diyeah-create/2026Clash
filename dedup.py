import yaml
import hashlib

with open('raw_proxies.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}

proxies = data.get('proxies', [])
seen = {}
unique = []

for p in proxies:
    if not isinstance(p, dict):
        continue
    server = p.get('server', '')
    name = p.get('name', '')

    # 过滤垃圾节点
    if not server or server.startswith(('127.', '192.168.', '10.')):
        continue
    if '防范境外势力渗透' in name or '本地' in name or p.get('uuid') == '00000000-0000-4000-8000-000000000000':
        continue

    # 去重
    key = hashlib.md5(f"{p.get('type')}|{server}|{p.get('port')}|{p.get('password') or p.get('uuid') or ''}".encode()).hexdigest()
    if key not in seen:
        seen[key] = True
        unique.append(p)

data['proxies'] = unique
with open('proxies_dedup.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)

print(f"去重+过滤完成: {len(proxies)} → {len(unique)} 个节点")
