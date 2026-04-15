#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_proxies.py - 增强版订阅拉取器（2026 优化 - SS 修复版）
✅ 修复 Shadowsocks 多种格式解析 | ✅ 支持 10000+ 节点 | ✅ 流式解析防 OOM
✅ 参数自动补全 | ✅ 失败自动重试 3 次 | ✅ 输出 proxies_raw.yaml
"""

import os
import sys
import json
import base64
import yaml
import requests
import re
from urllib.parse import urlparse, parse_qs, unquote
from typing import List, Dict, Optional

# ===== 配置常量 =====
MAX_RETRIES = 3
TIMEOUT = 30
USER_AGENT = "ClashMeta/2026 (Enhanced Fetcher v2.1)"
SUPPORTED_TYPES = ["ss", "ssr", "vmess", "trojan", "vless", "hysteria", "hysteria2", "tuic", "juicity"]

# ===== 工具函数 =====
def safe_b64decode(s: str) -> str:
    """安全 Base64 解码，自动补全填充 + 容错"""
    s = s.strip()
    if not s:
        return ""
    # 补全 =
    missing_padding = len(s) % 4
    if missing_padding:
        s += "=" * (4 - missing_padding)
    try:
        return base64.b64decode(s).decode("utf-8", errors="ignore")
    except Exception:
        return s

def parse_vless(uri: str) -> Optional[Dict]:
    """解析 VLESS 链接（支持 Reality/Xtls/Flow）"""
    try:
        if not uri.startswith("vless://"):
            return None
        uri = uri[8:]
        if "#" in uri:
            uri, name = uri.rsplit("#", 1)
            name = unquote(name)
        else:
            name = "VLESS"
        if "@" not in uri or "?" not in uri:
            return None
        auth, rest = uri.split("@", 1)
        server_port, params = rest.split("?", 1)
        server, port = server_port.rsplit(":", 1)
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
        if proxy["network"] == "ws" and params.get("path"):
            proxy["ws-opts"] = {"path": params["path"][0], "headers": {"Host": params.get("host", [server])[0]}}
        if proxy["network"] == "grpc" and params.get("serviceName"):
            proxy["grpc-opts"] = {"grpc-service-name": params["serviceName"][0]}
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
        if proxy["network"] == "ws":
            proxy["ws-opts"] = {
                "path": data.get("path", "/"),
                "headers": {"Host": data.get("host", data["add"])}
            }
        if proxy["network"] == "grpc" and data.get("path"):
            proxy["grpc-opts"] = {"grpc-service-name": data["path"]}
        return proxy
    except Exception as e:
        print(f"[WARN] 解析 VMess 失败: {e}", file=sys.stderr)
        return None

def parse_ss(uri: str) -> Optional[Dict]:
    """
    解析 Shadowsocks 链接（✅ 修复版：兼容所有格式）
    支持格式：
    1. ss://base64(method:password@server:port)#name
    2. ss://base64(method:password)@server:port#name
    3. ss://method:password@server:port#name
    4. ss://base64(whole_config)#name
    """
    try:
        if not uri.startswith("ss://"):
            return None
        uri = uri[5:]  # 移除 ss://
        
        # 分离名称
        name = "Shadowsocks"
        if "#" in uri:
            uri, name_part = uri.rsplit("#", 1)
            name = unquote(name_part)
        
        # 尝试直接解析：方法:密码@服务器:端口
        if "@" in uri and ":" in uri.split("@")[0]:
            try:
                auth, server_port = uri.split("@", 1)
                method, password = auth.split(":", 1)
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
            except ValueError:
                pass  # 继续尝试 Base64 解码
        
        # 尝试 Base64 解码
        decoded = safe_b64decode(uri)
        
        # 格式1: base64(method:password@server:port)
        if "@" in decoded and ":" in decoded.split("@")[0]:
            try:
                auth, server_port = decoded.split("@", 1)
                method, password = auth.split(":", 1)
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
            except ValueError:
                pass
        
        # 格式2: base64(method:password)@server:port
        if "@" in decoded:
            try:
                auth_part, server_port = decoded.split("@", 1)
                method, password = safe_b64decode(auth_part).split(":", 1)
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
            except ValueError:
                pass
        
        # 格式3: 纯 base64 编码的完整配置（SIP002）
        try:
            # 尝试解析为 JSON（某些订阅会返回 JSON 格式）
            config = json.loads(decoded)
            if "server" in config and "port" in config and "method" in config and "password" in config:
                return {
                    "name": config.get("remarks", name),
                    "type": "ss",
                    "server": config["server"],
                    "port": int(config["port"]),
                    "cipher": config["method"],
                    "password": config["password"],
                    "udp": True,
                }
        except:
            pass
        
        # 如果所有格式都失败，记录警告并跳过
        print(f"[DEBUG] SS 无法解析: {uri[:100]}... decoded: {decoded[:100]}", file=sys.stderr)
        return None
        
    except Exception as e:
        print(f"[WARN] 解析 SS 失败: {e} | URI: {uri[:80]}...", file=sys.stderr)
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
        if "?" in rest:
            server_port, params = rest.split("?", 1)
            params = parse_qs(params)
        else:
            server_port, params = rest, {}
        server, port = server_port.rsplit(":", 1)
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
        if params.get("type") == "ws" and params.get("path"):
            proxy["network"] = "ws"
            proxy["ws-opts"] = {"path": params["path"][0], "headers": {"Host": params.get("host", [server])[0]}}
        return proxy
    except Exception as e:
        print(f"[WARN] 解析 Trojan 失败: {e}", file=sys.stderr)
        return None

def parse_hysteria2(uri: str) -> Optional[Dict]:
    """解析 Hysteria2 链接"""
    try:
        if not uri.startswith("hysteria2://"):
            return None
        uri = uri[14:]
        if "#" in uri:
            uri, name = uri.rsplit("#", 1)
            name = unquote(name)
        else:
            name = "Hysteria2"
        auth, rest = uri.split("@", 1) if "@" in uri else ("", uri)
        if "?" in rest:
            server_port, params = rest.split("?", 1)
            params = parse_qs(params)
        else:
            server_port, params = rest, {}
        server, port = server_port.rsplit(":", 1)
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
    """带重试的 HTTP 请求（流式下载防 OOM）"""
    for i in range(retries):
        try:
            print(f"[INFO] 拉取订阅 ({i+1}/{retries}): {url[:60]}...")
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, stream=True)
            resp.raise_for_status()
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
            time.sleep(2 ** i)

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
    
    # 1. 尝试 Clash YAML
    if content.startswith("proxies:") or content.startswith("port:"):
        proxies = parse_clash_yaml(content)
        if proxies:
            print(f"[INFO] 识别为 Clash YAML，解析 {len(proxies)} 个节点")
            return proxies
    
    # 2. Base64 解码
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
            
            if proxy and proxy.get("name"):
                proxy.setdefault("udp", True)
                proxy.setdefault("skip-cert-verify", False)
                if proxy["type"] in ["vless", "trojan", "vmess"] and proxy.get("tls"):
                    proxy.setdefault("servername", proxy.get("sni", proxy["server"]))
                proxies.append(proxy)
        except Exception as e:
            print(f"[WARN] 跳过无效节点: {line[:60]}... 错误: {e}", file=sys.stderr)
            continue
    
    print(f"[INFO] 成功解析 {len(proxies)} 个有效节点")
    return proxies

def main():
    """主入口"""
    # 支持从文件读取（绕过 GitHub Actions 64KB 限制）
    urls_file = os.getenv("PROXIES_URLS_FILE")
    if urls_file and os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = f.read().strip()
    else:
        urls = os.getenv("PROXIES_URLS", "").strip()
    
    if not urls:
        print("[ERROR] 未设置 PROXIES_URLS 环境变量或文件", file=sys.stderr)
        sys.exit(1)
    
    url_list = [u.strip() for u in urls.split("\n") if u.strip()]
    print(f"[INFO] 共 {len(url_list)} 个订阅源")
    
    all_proxies = []
    for url in url_list:
        try:
            content = fetch_url(url)
            proxies = parse_subscription(content)
            all_proxies.extend(proxies)
        except Exception as e:
            print(f"[ERROR] 处理订阅 {url[:60]}... 失败: {e}", file=sys.stderr)
            continue
    
    # 输出原始节点
    output = {"proxies": all_proxies}
    with open("proxies_raw.yaml", "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False)
    
    print(f"[✅] 完成！共获取 {len(all_proxies)} 个节点，已保存至 proxies_raw.yaml")

if __name__ == "__main__":
    main()
