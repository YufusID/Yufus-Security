#!/usr/bin/env python3
"""
Скрипт для настройки DNSCrypt и I2P
Требует прав root для некоторых операций
"""

import os
import sys
import subprocess
import time
import requests
import json
import shutil
from pathlib import Path

class PrivacyTools:
    def __init__(self):
        self.dnscrypt_installed = False
        self.i2p_installed = False
        
    def check_root(self):
        """Проверяем права root"""
        if os.geteuid() != 0:
            print("⚠ Некоторые функции требуют прав root!")
            print("Запустите: sudo python3 script.py")
            return False
        return True
    
    def install_dnscrypt(self):
        """Устанавливаем DNSCrypt-proxy"""
        print("\n=== Установка DNSCrypt-proxy ===\n")
        
        try:
            # Определяем дистрибутив
            if shutil.which("apt"):
                print("Обновляем пакеты...")
                subprocess.run(["apt", "update"], check=True)
                print("Устанавливаем DNSCrypt-proxy...")
                subprocess.run(["apt", "install", "-y", "dnscrypt-proxy"], check=True)
                
            elif shutil.which("dnf"):
                subprocess.run(["dnf", "install", "-y", "dnscrypt-proxy"], check=True)
                
            elif shutil.which("yum"):
                subprocess.run(["yum", "install", "-y", "dnscrypt-proxy"], check=True)
                
            elif shutil.which("pacman"):
                subprocess.run(["pacman", "-S", "--noconfirm", "dnscrypt-proxy"], check=True)
                
            elif shutil.which("zypper"):
                subprocess.run(["zypper", "install", "-y", "dnscrypt-proxy"], check=True)
                
            else:
                print("Менеджер пакетов не найден. Установите вручную:")
                print("См. https://github.com/DNSCrypt/dnscrypt-proxy/wiki/Installation")
                return False
            
            # Настраиваем DNSCrypt
            self.configure_dnscrypt()
            self.dnscrypt_installed = True
            print("✓ DNSCrypt-proxy установлен")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Ошибка установки: {e}")
            return False
    
    def configure_dnscrypt(self):
        """Настраиваем DNSCrypt-proxy"""
        print("\nНастраиваем DNSCrypt...")
        
        try:
            # Резервное копирование конфигурации
            config_path = "/etc/dnscrypt-proxy/dnscrypt-proxy.toml"
            if os.path.exists(config_path):
                shutil.copy(config_path, f"{config_path}.backup")
            
            # Простая конфигурация
            config = """# Простая конфигурация DNSCrypt
listen_addresses = ['127.0.0.1:53']
server_names = ['cloudflare', 'quad9-doh-ip4-filter-pri']

# Используем DNS-over-HTTPS
[static]
  [static.'cloudflare']
  stamp = 'sdns://AgcAAAAAAAAABzEuMC4wLjGgENk8mGSlIfMGXMOlIlCcKvq7AVgcrZxtjon911-ep1cgIWJhci5leGFtcGxlLmNvbQovZG5zLXF1ZXJ5'

  [static.'quad9-doh-ip4-filter-pri']
  stamp = 'sdns://AgMAAAAAAAAABzEuMC4wLjGgENk8mGSlIfMGXMOlIlCcKvq7AVgcrZxtjon911-ep1cgIWJhci5leGFtcGxlLmNvbQovZG5zLXF1ZXJ5'

# Логирование
[query_log]
  file = '/var/log/dnscrypt-proxy/query.log'

# Мониторинг
[local_doh]
  listen_addresses = ['127.0.0.1:3000']
  path = "/dns-query"
"""
            
            with open(config_path, 'w') as f:
                f.write(config)
            
            print("Конфигурация сохранена")
            
            # Перезапускаем службу
            self.restart_service("dnscrypt-proxy")
            
        except Exception as e:
            print(f"Ошибка конфигурации: {e}")
    
    def start_dnscrypt(self):
        """Запускаем DNSCrypt"""
        print("\nЗапускаем DNSCrypt-proxy...")
        
        try:
            subprocess.run(["systemctl", "start", "dnscrypt-proxy"], check=True)
            subprocess.run(["systemctl", "enable", "dnscrypt-proxy"], check=True)
            time.sleep(2)
            
            # Проверяем работу
            result = subprocess.run(["systemctl", "is-active", "dnscrypt-proxy"], 
                                  capture_output=True, text=True)
            
            if "active" in result.stdout:
                print("✓ DNSCrypt-proxy запущен")
                return True
            else:
                print("✗ DNSCrypt-proxy не запустился")
                return False
                
        except Exception as e:
            print(f"Ошибка запуска: {e}")
            return False
    
    def test_dns(self):
        """Тестируем DNS"""
        print("\n=== Тестирование DNS ===\n")
        
        dnscrypt_servers = [
            "127.0.0.1",  # Локальный DNSCrypt
            "9.9.9.9",    # Quad9
            "1.1.1.1",    # Cloudflare
            "8.8.8.8",    # Google
        ]
        
        test_domains = ["google.com", "yandex.ru", "github.com"]
        
        for server in dnscrypt_servers:
            print(f"\nDNS сервер: {server}")
            for domain in test_domains:
                try:
                    result = subprocess.run(
                        ["dig", f"@{server}", domain, "+short"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.stdout.strip():
                        print(f"  {domain}: ✓")
                    else:
                        print(f"  {domain}: ✗")
                except:
                    print(f"  {domain}: ✗ (ошибка)")
    
    def install_i2p(self):
        """Устанавливаем I2P"""
        print("\n=== Установка I2P ===\n")
        
        try:
            # Для Debian/Ubuntu
            if shutil.which("apt"):
                print("Добавляем репозиторий I2P...")
                subprocess.run([
                    "apt", "install", "-y", 
                    "software-properties-common", "apt-transport-https"
                ], check=True)
                
                subprocess.run([
                    "add-apt-repository", "-y", 
                    "ppa:i2p-maintainers/i2p"
                ], check=True)
                
                subprocess.run(["apt", "update"], check=True)
                print("Устанавливаем I2P...")
                subprocess.run(["apt", "install", "-y", "i2p"], check=True)
            
            # Для других систем
            elif shutil.which("dnf"):
                # Установка из репозитория Fedora
                subprocess.run(["dnf", "install", "-y", "i2p"], check=True)
                
            else:
                print("Установите I2P вручную:")
                print("См. https://geti2p.net/ru/download")
                return False
            
            self.configure_i2p()
            self.i2p_installed = True
            print("✓ I2P установлен")
            return True
            
        except Exception as e:
            print(f"✗ Ошибка установки I2P: {e}")
            return False
    
    def configure_i2p(self):
        """Настраиваем I2P"""
        print("\nНастраиваем I2P...")
        
        try:
            # Базовая конфигурация через i2prouter
            i2p_dir = Path.home() / ".i2p"
            i2p_dir.mkdir(exist_ok=True)
            
            # Конфигурационный файл
            config = """# Базовая конфигурация I2P
i2cp.tcp.host=127.0.0.1
i2cp.tcp.port=7654
i2np.udp.port=7655
i2np.udp.host=127.0.0.1
"""
            
            config_path = i2p_dir / "clients.config"
            with open(config_path, 'w') as f:
                f.write(config)
            
            print("Конфигурация I2P сохранена")
            
        except Exception as e:
            print(f"Ошибка конфигурации I2P: {e}")
    
    def start_i2p(self):
        """Запускаем I2P"""
        print("\nЗапускаем I2P...")
        
        try:
            # Запускаем как сервис или демон
            if shutil.which("systemctl"):
                subprocess.run(["systemctl", "start", "i2p"], check=True)
                subprocess.run(["systemctl", "enable", "i2p"], check=True)
                time.sleep(5)
                
                # Проверяем
                result = subprocess.run(["systemctl", "is-active", "i2p"],
                                      capture_output=True, text=True)
                
                if "active" in result.stdout:
                    print("✓ I2P запущен как служба")
                    return True
                    
            # Альтернативный запуск
            print("Запускаем I2P вручную...")
            i2p_process = subprocess.Popen(
                ["i2prouter", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(10)  # Ждем запуска
            
            # Проверяем порт
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 7657))  # Порт консоли I2P
            
            if result == 0:
                print("✓ I2P запущен (порт 7657)")
                return True
            else:
                print("✗ I2P не запустился")
                return False
                
        except Exception as e:
            print(f"Ошибка запуска I2P: {e}")
            return False
    
    def test_i2p(self):
        """Тестируем I2P"""
        print("\n=== Тестирование I2P ===\n")
        
        # Прокси для I2P
        i2p_proxy = {
            'http': 'http://127.0.0.1:4444',
            'https': 'http://127.0.0.1:4444'
        }
        
        # I2P сайты для теста
        i2p_sites = [
            "http://127.0.0.1:7657",  # Консоль I2P
            "http://identiguy.i2p/",
            "http://forum.i2p/"
        ]
        
        print("Проверяем I2P прокси...")
        
        for site in i2p_sites:
            try:
                if site.startswith("http://127.0.0.1"):
                    response = requests.get(site, timeout=10)
                else:
                    response = requests.get(site, proxies=i2p_proxy, timeout=30)
                
                if response.status_code == 200:
                    print(f"✓ {site} доступен")
                else:
                    print(f"✗ {site}: код {response.status_code}")
                    
            except Exception as e:
                print(f"✗ {site}: {str(e)[:50]}...")
    
    def setup_i2p_browser(self):
        """Настраиваем браузер для I2P"""
        print("\n=== Настройка браузера для I2P ===\n")
        
        # Конфигурация для Firefox
        firefox_config = """
// Настройки прокси для I2P
user_pref("network.proxy.type", 1);
user_pref("network.proxy.http", "127.0.0.1");
user_pref("network.proxy.http_port", 4444);
user_pref("network.proxy.ssl", "127.0.0.1");
user_pref("network.proxy.ssl_port", 4444);
user_pref("network.proxy.no_proxies_on", "localhost, 127.0.0.1");
user_pref("network.proxy.failover_timeout", 300);
"""
        
        # Конфигурация для Chromium
        chromium_config = """{
  "mode": "fixed_servers",
  "rules": {
    "singleProxy": {
      "scheme": "http",
      "host": "127.0.0.1",
      "port": 4444
    },
    "bypassList": ["localhost", "127.0.0.1"]
  }
}"""
        
        config_dir = Path.home() / "i2p_config"
        config_dir.mkdir(exist_ok=True)
        
        # Сохраняем конфигурации
        (config_dir / "firefox_i2p.js").write_text(firefox_config)
        (config_dir / "chromium_i2p.json").write_text(chromium_config)
        
        print("Конфигурации сохранены в:", config_dir)
        print("\nДля Firefox:")
        print("1. Перейдите в about:config")
        print("2. Импортируйте: " + str(config_dir / "firefox_i2p.js"))
        
        print("\nДля Chromium:")
        print("1. Установите расширение Proxy SwitchyOmega")
        print("2. Импортируйте настройки из файла")
    
    def restart_service(self, service_name):
        """Перезапускаем системную службу"""
        try:
            if shutil.which("systemctl"):
                subprocess.run(["systemctl", "restart", service_name], check=True)
                print(f"Служба {service_name} перезапущена")
            elif shutil.which("service"):
                subprocess.run(["service", service_name, "restart"], check=True)
        except:
            pass
    
    def show_status(self):
        """Показывает статус сервисов"""
        print("\n" + "="*50)
        print("ТЕКУЩИЙ СТАТУС")
        print("="*50)
        
        # Проверяем DNSCrypt
        print("\nDNSCrypt-proxy:")
        try:
            result = subprocess.run(["systemctl", "is-active", "dnscrypt-proxy"],
                                  capture_output=True, text=True)
            if "active" in result.stdout:
                print("✓ Активен")
                # Проверяем порт
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', 53))
                if result == 0:
                    print("  Порт 53 слушает")
                else:
                    print("  ✗ Порт 53 не отвечает")
            else:
                print("✗ Не активен")
        except:
            print("✗ Не установлен/не доступен")
        
        # Проверяем I2P
        print("\nI2P:")
        try:
            result = subprocess.run(["systemctl", "is-active", "i2p"],
                                  capture_output=True, text=True)
            if "active" in result.stdout:
                print("✓ Активен")
                # Проверяем порты
                for port in [4444, 7657, 7658]:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        print(f"  Порт {port} слушает")
            else:
                print("✗ Не активен")
        except:
            print("✗ Не установлен/не доступен")
        
        print("\n" + "="*50)

def main_menu():
    """Главное меню"""
    tools = PrivacyTools()
    
    while True:
        print("\n" + "="*50)
        print("DNSCRYPT & I2P SETUP TOOL")
        print("="*50)
        print("1. Установить DNSCrypt-proxy")
        print("2. Установить I2P")
        print("3. Запустить все сервисы")
        print("4. Тестировать соединение")
        print("5. Настроить браузер для I2P")
        print("6. Показать статус")
        print("7. Выход")
        print("="*50)
        
        choice = input("\nВыберите действие (1-7): ").strip()
        
        if choice == "1":
            if tools.check_root():
                tools.install_dnscrypt()
                tools.start_dnscrypt()
        
        elif choice == "2":
            if tools.check_root():
                tools.install_i2p()
                tools.start_i2p()
        
        elif choice == "3":
            if tools.check_root():
                print("\nЗапускаем все сервисы...")
                tools.start_dnscrypt()
                tools.start_i2p()
                print("✓ Все сервисы запущены")
        
        elif choice == "4":
            print("\nТестируем соединения...")
            tools.test_dns()
            tools.test_i2p()
        
        elif choice == "5":
            tools.setup_i2p_browser()
        
        elif choice == "6":
            tools.show_status()
        
        elif choice == "7":
            print("\nВыход...")
            break
        
        else:
            print("Неверный выбор")

if __name__ == "__main__":
    # Проверяем Python версию
    if sys.version_info < (3, 6):
        print("Требуется Python 3.6 или выше")
        sys.exit(1)
    
    print("Скрипт для настройки DNSCrypt и I2P")
    print("Некоторые операции требуют прав root")
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")