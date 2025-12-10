import os
import subprocess
import time
import requests
import random

class SimpleVPN:
    def __init__(self):
        self.vpn_process = None
        
    def get_free_vpn_configs(self):
        """Получаем список бесплатных VPN серверов"""
        # Некоторые публичные VPN конфигурации
        vpn_servers = [
            {
                'name': 'VPN Server 1',
                'config_url': 'https://www.vpngate.net/api/iphone/',
                'type': 'openvpn'
            },
            {
                'name': 'VPN Server 2', 
                'config_url': 'https://freevpn.me/accounts/',
                'type': 'openvpn'
            }
        ]
        return vpn_servers
    
    def download_openvpn_config(self, url):
        """Скачиваем OpenVPN конфигурацию"""
        try:
            print("Скачиваем конфигурацию VPN...")
            response = requests.get(url, timeout=10)
            
            # Сохраняем конфигурацию
            with open('vpn_config.ovpn', 'w') as f:
                f.write(response.text)
            
            print("Конфигурация сохранена")
            return True
            
        except Exception as e:
            print(f"Ошибка скачивания: {e}")
            return False
    
    def connect_openvpn(self, config_file='vpn_config.ovpn'):
        """Подключаемся через OpenVPN"""
        try:
            print("Подключаемся к VPN...")
            
            # Для OpenVPN нужны права root
            if os.geteuid() != 0:
                print("Для OpenVPN нужны права root!")
                print("Запустите: sudo python3 script.py")
                return False
            
            # Запускаем OpenVPN
            self.vpn_process = subprocess.Popen(
                ['openvpn', '--config', config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print("Ждем подключения...")
            time.sleep(10)
            
            # Проверяем IP
            self.check_connection()
            return True
            
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def check_connection(self):
        """Проверяем подключение"""
        try:
            print("\nПроверяем соединение...")
            
            # Без VPN
            original_ip = requests.get('https://api.ipify.org', timeout=5).text
            print(f"Оригинальный IP: {original_ip}")
            
            # Через VPN (ждем немного)
            time.sleep(3)
            vpn_ip = requests.get('https://api.ipify.org', timeout=10).text
            print(f"IP через VPN: {vpn_ip}")
            
            if original_ip != vpn_ip:
                print("✓ VPN работает!")
            else:
                print("⚠ Возможно, VPN не работает")
                
        except Exception as e:
            print(f"Ошибка проверки: {e}")
    
    def disconnect(self):
        """Отключаем VPN"""
        if self.vpn_process:
            print("Отключаем VPN...")
            self.vpn_process.terminate()
            self.vpn_process = None
            print("VPN отключен")

def main():
    vpn = SimpleVPN()
    
    print("=== VPN Security by Юфус ===\n")
    
    # Показываем доступные серверы
    servers = vpn.get_free_vpn_configs()
    print("Доступные VPN серверы:")
    for i, server in enumerate(servers, 1):
        print(f"{i}. {server['name']}")
    
    try:
        choice = int(input("\nВыберите сервер (1-2): "))
        
        if choice == 1:
            print("\nИспользуем VPN Gate (Япония)")
            # Скачиваем конфигурацию
            config_data = requests.get('https://www.vpngate.net/api/iphone/').text
            servers = config_data.split('\n')[1:]  # Пропускаем заголовок
            
            if servers:
                # Берем первый рабочий сервер
                server_config = servers[0].split(',')[-1]
                import base64
                config = base64.b64decode(server_config).decode('utf-8')
                
                with open('vpn_config.ovpn', 'w') as f:
                    f.write(config)
                
                print("Конфигурация загружена")
                
                # Запускаем VPN
                vpn.connect_openvpn()
            else:
                print("Не удалось получить серверы")
                
        elif choice == 2:
            print("\nЭто демо. На практике нужна реальная конфигурация")
            print("Установите OpenVPN и скачайте конфигурации с:")
            print("1. https://www.vpngate.net")
            print("2. https://freevpn.me")
            print("3. Или купите VPN сервис")
            
    except KeyboardInterrupt:
        print("\n\nОтмена")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        vpn.disconnect()

if __name__ == "__main__":
    main()