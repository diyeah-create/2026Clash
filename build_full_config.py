import yaml
import re

# 加载测速后的 proxies.yaml（仅 proxies 列表）
with open('proxies.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

# 构建全网最强配置（Loyalsoldier 规则集，每日自动更新）
config = {
    'mixed-port': 7890,
    'allow-lan': True,
    'mode': 'rule',
    'log-level': 'info',
    'unified-delay': True,
    'tcp-concurrent': True,
    'ipv6': False,
    'proxies': proxies,

    'proxy-groups': [
        {
            'name': '自动选择',
            'type': 'url-test',
            'proxies': [p['name'] for p in proxies],
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300,
            'tolerance': 50
        },
        {
            'name': '手动选择',
            'type': 'select',
            'proxies': [p['name'] for p in proxies]
        },
        {
            'name': 'PROXY',
            'type': 'select',
            'proxies': ['自动选择', '手动选择', 'DIRECT']
        }
    ],

    'rule-providers': {
        'reject': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt', 'path': './ruleset/reject.yaml', 'interval': 86400},
        'private': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/private.txt', 'path': './ruleset/private.yaml', 'interval': 86400},
        'cncidr': {'type': 'http', 'behavior': 'ipcidr', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt', 'path': './ruleset/cncidr.yaml', 'interval': 86400},
        'lancidr': {'type': 'http', 'behavior': 'ipcidr', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt', 'path': './ruleset/lancidr.yaml', 'interval': 86400},
        'applications': {'type': 'http', 'behavior': 'classical', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt', 'path': './ruleset/applications.yaml', 'interval': 86400},
        'apple': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/apple.txt', 'path': './ruleset/apple.yaml', 'interval': 86400},
        'icloud': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/icloud.txt', 'path': './ruleset/icloud.yaml', 'interval': 86400},
        'gfw': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/gfw.txt', 'path': './ruleset/gfw.yaml', 'interval': 86400},
        'proxy': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt', 'path': './ruleset/proxy.yaml', 'interval': 86400},
        'direct': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt', 'path': './ruleset/direct.yaml', 'interval': 86400},
        'tld-not-cn': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/tld-not-cn.txt', 'path': './ruleset/tld-not-cn.yaml', 'interval': 86400},
        'telegramcidr': {'type': 'http', 'behavior': 'ipcidr', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/telegramcidr.txt', 'path': './ruleset/telegramcidr.yaml', 'interval': 86400},
    },

    'rules': [
        'RULE-SET,reject,REJECT',
        'RULE-SET,private,DIRECT',
        'RULE-SET,cncidr,DIRECT',
        'RULE-SET,lancidr,DIRECT',
        'RULE-SET,applications,DIRECT',
        'RULE-SET,apple,DIRECT',
        'RULE-SET,icloud,DIRECT',
        'RULE-SET,gfw,PROXY',
        'RULE-SET,proxy,PROXY',
        'RULE-SET,direct,DIRECT',
        'RULE-SET,tld-not-cn,PROXY',
        'GEOIP,CN,DIRECT',
        'MATCH,PROXY'
    ]
}

with open('proxies.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print(f"✅ 全网最强配置生成完成！节点数量: {len(proxies)} | 规则集: Loyalsoldier（每日自动更新）")
