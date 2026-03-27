#!/usr/bin/env python3
import requests
import base64
import re
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# ========== НАСТРОЙКИ ==========
# СЮДА ВСТАВЬ СВОИ ССЫЛКИ НА ИСТОЧНИКИ С КЛЮЧАМИ
SOURCES = [
    "https://github.com/igareck/vpn-configs-for-russia",   # Замени на реальную ссылку
]

# Технические настройки (можно не менять)
CHECK_TIMEOUT = 3
MAX_WORKERS = 20

# ========== ФУНКЦИИ ==========

def fetch_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        try:
            decoded = base64.b64decode(response.text).decode('utf-8')
            return decoded
        except:
            return response.text
    except Exception as e:
        print(f"Ошибка загрузки {url}: {e}")
        return ""

def extract_server_from_key(key):
    match = re.search(r'@([^:]+):(\d+)', key)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def check_port(host, port, timeout=CHECK_TIMEOUT):
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except:
        return False

def check_key(key):
    host, port = extract_server_from_key(key)
    if host and port:
        if check_port(host, port):
            return key
    return None

def gather_keys():
    all_keys = []
    for url in SOURCES:
        print(f"Загружаю {url}...")
        content = fetch_from_url(url)
        if content:
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    all_keys.append(line)
    return all_keys

def check_keys_parallel(keys):
    print(f"Проверяю {len(keys)} ключей...")
    working = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_key, key): key for key in keys}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                working.append(result)
            if (i + 1) % 50 == 0:
                print(f"  Проверено {i + 1}/{len(keys)} ключей")
    print(f"Найдено рабочих: {len(working)}")
    return working

def generate_karing_subscription(keys, filename="karing_subscription.txt"):
    with open(filename, "w") as f:
        f.write("#profile-title: Авто-ключи\n")
        f.write("#profile-update-interval: 5\n")   # 5 часов — то, что нужно
        f.write("#profile-web-page-url: https://github.com/naivon85-source/vpn-auto-updater\n")
        f.write("\n")
        for key in keys:
            f.write(key + "\n")
    print(f"Файл {filename} создан. Karing будет обновляться каждые 5 часов.")

def main():
    print("=== Автообновление ключей для Karing ===\n")
    all_keys = gather_keys()
    print(f"Всего ключей собрано: {len(all_keys)}")
    if not all_keys:
        print("Не найдено ключей. Проверь источники.")
        return
    working_keys = check_keys_parallel(all_keys)
    if not working_keys:
        print("Не найдено рабочих ключей.")
        return
    generate_karing_subscription(working_keys)
    print("\n=== Готово! Файл обновлён. ===")

if __name__ == "__main__":
    main()
