import yaml
import re

with open('proxies_temp.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}

proxies = data.get('proxies', [])

for p in proxies:
    if not isinstance(p, dict):
        continue
    
    old_name = p.get('name', '')
    
    # 提取已有速度信息（如 ⬇️ 15.67MB/s）
    speed_match = re.search(r'⬇️\s*([\d.]+)MB/s', old_name)
    speed_str = speed_match.group(0) if speed_match else ''
    
    # 获取延迟（clash-speedtest 最新版已支持 latency 字段）
    latency = p.get('latency') or p.get('ping') or 0
    if isinstance(latency, (int, float)) and latency > 0:
        latency_str = f" | ⚡ {int(latency)}ms"
    else:
        latency_str = ""
    
    # 构建新名称：保留国旗+速度，并追加延迟
    if speed_str:
        new_name = old_name.replace(speed_str, f"{speed_str}{latency_str}")
    else:
        new_name = f"{old_name}{latency_str}"
    
    # 清理多余的分隔符
    new_name = re.sub(r'\s*\|\s*\|', ' |', new_name).strip()
    p['name'] = new_name

data['proxies'] = proxies

with open('proxies.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)

print(f"节点名增强完成（加入延迟），共处理 {len(proxies)} 个节点")
