import yaml
import glob
import os

all_proxies = []

# 更改 glob 模式以匹配 actions/download-artifact 的行为
# 它会将每个 artifact 下载到 path/artifact-name/ 目录下
# 所以我们需要查找 chunks/*/proxies_tested_chunk_*.yaml
for f in glob.glob("chunks/*/proxies_tested_chunk_*.yaml"):
    with open(f, 'r', encoding='utf-8') as fp:
        data = yaml.safe_load(fp) or {}
    all_proxies.extend(data.get('proxies', []))

with open("proxies_tested.yaml", "w", encoding="utf-8") as f:
    yaml.dump({'proxies': all_proxies}, f, allow_unicode=True, sort_keys=False)

print(f"✅ {len(all_proxies)} 个 fast 分片合并完成！共 {len(all_proxies)} 个节点")
