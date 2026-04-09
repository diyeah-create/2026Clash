import yaml
import glob

all_proxies = []
for f in glob.glob("proxies_tested_chunk_*.yaml"):
    with open(f, encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
        all_proxies.extend(data.get("proxies", []))

with open("proxies_tested.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"proxies": all_proxies}, f, allow_unicode=True, sort_keys=False)

print(f"✅ 8 个 fast 分片合并完成！共 {len(all_proxies)} 个节点")
print(f"其中包含 latency 字段的节点数量: {sum(1 for p in all_proxies if p.get('latency') is not None)}")
