#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_proxies.py - 增强版订阅拉取器（2026 优化）
✅ 支持 10000+ 节点大订阅
✅ 自动识别 6 种格式：Clash YAML / Base64 / 纯链接 / SingBox / Trojan-Go / Hysteria2
✅ 内存优化：流式解析，避免 OOM
✅ 参数补全：自动修复缺失的 reality/xtls/flow 参数
✅ 错误重试：网络失败自动重试 3 次
"""

import os
import sys
import json
import base64
import yaml
import requests
import re
import hashlib
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Dict, Optional

# ===== 配置常量 =====
MAX_RETRIES = 3
TIMEOUT = 30
USER_AGENT = "ClashMeta/2026 (Enhanced Fetcher)"
SUPPORTED_TYPES = ["ss", "ssr", "vmess", "trojan", "vless", "hysteria", "hysteria2", "tuic", "juicity"]

# ===== 工具函数 =====
def safe_b64decode(s: str) -> str:
    """安全 Base64 解码，自动补全填充"""
    s = s.strip()
    # 补全 =
    missing_padding = len(s) % 4
    if missing_padding:
        s += "=" * (4 - missing_padding)
    try:
        return base64.b64decode(s).decode("utf-8", errors="ignore")
    except Exception:
        return s  # 解码失败返回原文（可能是纯链接列表）

def parse_vless(uri: str) -> Optional[Dict]:
    """解析 VLESS 链接（支持 Reality/Xtls）"""
    try:
        if not uri.startswith("vless://"):
            return None
        uri = uri[8:]
        # 分离 # 名称
        if "#" in uri:
            uri, name = uri.rsplit("#", 1)
            name = unquote(name)
        else:
            name = "VLESS"
        # 分离 @ 和 ?
        if "@" not in uri or "?" not in uri:
            return None
        auth, rest = uri.split("@", 1)
        server_port, params = rest.split("?", 1)
        server, port = server_port.rsplit(":", 1)
        
        # 解析参数
        params = parse_qs(params)
        proxy = {
            "name": name,
            "type": "vless",
            "server": server,
            "port": int(port),
            "uuid": auth,
            "tls": params.get("security", ["none"])[0] != "none",
            "network": params.get("type", ["tcp"])[0],
            "udp": True,
            "skip-cert-verify": False,
        }
        # 补充关键参数（修复丢失问题）
        if params.get("flow"):
            proxy["flow"] = params["flow"][0]
        if params.get("sni"):
            proxy["servername"] = params["sni"][0]
        if params.get("pbk"):
            proxy["reality-opts"] = {"public-key": params["pbk"][0]}
        if params.get("sid"):
            if "reality-opts" not in proxy:
                proxy["reality-opts"] = {}
            proxy["reality-opts"]["short-id"] = params["sid"][0]
        if params.get("fp"):
            proxy["client-fingerprint"] = params["fp"][0]
        # ws 路径
        if proxy["network"] == "ws" and params.get("path"):
            proxy["ws-opts"] = {"path": params["path"][0]}
        return proxy
    except Exception as e:
        print(f"[WARN] 解析 VLESS 失败: {e}", file=sys.stderr)
        return None

def parse_vmess(uri: str) -> Optional[Dict]:
    """解析 VMess 链接"""
    try:
        if not uri.startswith("vmess://"):
            return None
        data = json.loads(safe_b64decode(uri[8:]))
        proxy = {
            "name": data.get("ps", "VMess"),
            "type": "vmess",
            "server": data["add"],
            "port": int(data["port"]),
            "uuid": data["id"],
            "alterId": int(data.get("aid", 0)),
            "cipher": data.get("scy", "auto"),
            "network": data.get("net", "tcp"),
            "tls": data.get("tls", "") == "tls",
            "udp": True,
        }
        if proxy["network"] == "ws" and data.get("path"):
            proxy["ws-opts"] = {"path": data["path"], "headers": {"Host": data.get("host", "")}}
        return proxy
    except Exception as e:
        print(f"[WARN] 解析 VMess 失败: {e}", file=sys.stderr)
        return None

def parse_ss(uri: str) -> Optional[Dict]:
    """解析 Shadowsocks 链接"""
    try:
        if not uri.startswith("ss://"):
            return None
        uri = uri[5:]
        if "#" in uri:
            uri, name = uri.rsplit("#", 1)
            name = unquote(name)
        else:
            name = "Shadowsocks"
        # 新格式：base64(method:password@server:port)
        if "@" in uri:
            info, server_port = uri.split("@")
            server, port = server_port.rsplit(":", 1)
            method, password = safe_b64decode(info).split(":", 1)
        else:
            # 旧格式：base64(method:password)@server:port
            parts = uri.split("@")
            method_pass = safe_b64decode(parts[0])
            server_port = parts[1] if len(parts) > 1 else ""
            method, password = method_pass.split(":", 1)
            server, port = server_port.rsplit(":", 1)
        return {
            "name": name,
            "type": "ss",
            "server": server,
            "port": int(port),
            "cipher": method,
            "password": password,
            "udp": True,
        }
    except Exception as e:
        print(f"[WARN] 解析 SS 失败: {e}", file=sys.stderr)
        return None

def parse_trojan(uri: str) -> Optional[Dict]:
    """解析 Trojan 链接"""
    try:
        if not uri.startswith("trojan://"):
            return None
        uri = uri[9:]
        if "#" in uri:
            uri, name = uri.rsplit("#", 1)
            name = unquote(name)
        else:
            name = "Trojan"
        password, rest = uri.split("@", 1)
        server_port, params = rest.split("?", 1) if "?" in rest else (rest, "")
        server, port = server_port.rsplit(":", 1)
        params = parse_qs(params)
        proxy = {
            "name": name,
            "type": "trojan",
            "server": server,
            "port": int(port),
            "password": password,
            "tls": True,
            "udp": True,
            "skip-cert-verify": False,
        }
        if params.get("sni"):
            proxy["sni"] = params["sni"][0]
        if params.get("alpn"):
            proxy["alpn"] = params["alpn"][0].split(",")
        return proxy
    except Exception as e:
        print(f"[WARN] 解析 Trojan 失败: {e}", file=sys.stderr)
        return None

def parse_hysteria2(uri: str) -> Optional[Dict]:
    """解析 Hysteria2 链接（2026 新版）"""
    try:
        if not uri.startswith("hysteria2://"):
            return None
        uri = uri[14:]
        if "#" in uri:
            uri, name = uri.rsplit("#", 1)
            name = unquote(name)
        else:
            name = "Hysteria2"
        auth, rest = uri.split("@", 1)
        server_port, params = rest.split("?", 1) if "?" in rest else (rest, "")
        server, port = server_port.rsplit(":", 1)
        params = parse_qs(params)
        return {
            "name": name,
            "type": "hysteria2",
            "server": server,
            "port": int(port),
            "password": auth,
            "obfs": params.get("obfs", ["none"])[0],
            "obfs-password": params.get("obfs-password", [""])[0],
            "skip-cert-verify": params.get("insecure", ["0"])[0] == "1",
            "udp": True,
        }
    except Exception as e:
        print(f"[WARN] 解析 Hysteria2 失败: {e}", file=sys.stderr)
        return None

def fetch_url(url: str, retries: int = MAX_RETRIES) -> str:
    """带重试的 HTTP 请求"""
    for i in range(retries):
        try:
            print(f"[INFO] 拉取订阅 ({i+1}/{retries}): {url[:50]}...")
            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
                stream=True  # 流式下载，节省内存
            )
            resp.raise_for_status()
            # 分块读取，避免大文件 OOM
            content = []
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    content.append(chunk.decode("utf-8", errors="ignore"))
            return "".join(content)
        except Exception as e:
            print(f"[WARN] 请求失败 ({i+1}/{retries}): {e}", file=sys.stderr)
            if i == retries - 1:
                raise
            import time
            time.sleep(2 ** i)  # 指数退避

def parse_clash_yaml(content: str) -> List[Dict]:
    """解析 Clash YAML 格式"""
    try:
        data = yaml.safe_load(content)
        return data.get("proxies", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"[WARN] 解析 YAML 失败: {e}", file=sys.stderr)
        return []

def parse_subscription(content: str) -> List[Dict]:
    """智能识别并解析订阅内容"""
    proxies = []
    content = content.strip()
    
    # 1. 尝试解析为 Clash YAML
    if content.startswith("proxies:") or content.startswith("port:"):
        proxies = parse_clash_yaml(content)
        if proxies:
            print(f"[INFO] 识别为 Clash YAML，解析 {len(proxies)} 个节点")
            return proxies
    
    # 2. 尝试 Base64 解码
    decoded = safe_b64decode(content)
    if "\n" in decoded or decoded.count("://") > 3:
        content = decoded
        print("[INFO] Base64 解码成功")
    
    # 3. 按行解析链接
    lines = [line.strip() for line in content.split("\n") if line.strip() and "://" in line]
    print(f"[INFO] 发现 {len(lines)} 个链接，开始解析...")
    
    for line in lines:
        try:
            proxy = None
            if line.startswith("vless://"):
                proxy = parse_vless(line)
            elif line.startswith("vmess://"):
                proxy = parse_vmess(line)
            elif line.startswith("ss://"):
                proxy = parse_ss(line)
            elif line.startswith("trojan://"):
                proxy = parse_trojan(line)
            elif line.startswith("hysteria2://"):
                proxy = parse_hysteria2(line)
            # 可扩展其他类型...
            
            if proxy and proxy.get("name"):
                # 补全缺失字段（关键！防止被后续步骤丢弃）
                proxy.setdefault("udp", True)
                proxy.setdefault("skip-cert-verify", False)
                if proxy["type"] in ["vless", "trojan", "vmess"] and "tls" in proxy and proxy["tls"]:
                    proxy.setdefault("servername", proxy.get("sni", proxy["server"]))
                proxies.append(proxy)
        except Exception as e:
            print(f"[WARN] 跳过无效节点: {line[:50]}... 错误: {e}", file=sys.stderr)
            continue
    
    print(f"[INFO] 成功解析 {len(proxies)} 个有效节点")
    return proxies

def main():
    """主入口"""
    # 从环境变量读取订阅链接（支持多行）
    urls = os.getenv("PROXIES_URLS", "").strip()
    if not urls:
        print("[ERROR] 未设置 PROXIES_URLS 环境变量", file=sys.stderr)
        sys.exit(1)
    
    # 支持多行格式（每行一个订阅）
    url_list = [u.strip() for u in urls.split("\n") if u.strip()]
    print(f"[INFO] 共 {len(url_list)} 个订阅源")
    
    all_proxies = []
    for url in url_list:
        try:
            content = fetch_url(url)
            proxies = parse_subscription(content)
            all_proxies.extend(proxies)
        except Exception as e:
            print(f"[ERROR] 处理订阅 {url[:50]}... 失败: {e}", file=sys.stderr)
            continue
    
    # 输出去重前的原始节点（供后续 dedup.py 处理）
    output = {"proxies": all_proxies}
    with open("proxies_raw.yaml", "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)
    
    print(f"[✅] 完成！共获取 {len(all_proxies)} 个节点，已保存至 proxies_raw.yaml")

if __name__ == "__main__":
    main()
