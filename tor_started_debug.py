import requests
import subprocess
import time

# Автоматически запускаем Tor если он не запущен
def start_tor():
    print("Проверяем Tor...")
    
    # Проверяем, запущен ли Tor
    try:
        result = subprocess.run(['pgrep', 'tor'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Tor уже запущен")
            return True
    except:
        pass
    
    # Запускаем Tor
    print("Запускаем Tor...")
    try:
        # Фоновый запуск Tor
        subprocess.Popen(['tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Tor запускается...")
        time.sleep(10)  # Ждем запуска
        print("✓ Tor запущен")
        return True
    except Exception as e:
        print(f"✗ Ошибка запуска Tor: {e}")
        print("Установите Tor: sudo apt install tor")
        return False

# Проверяем IP
def check_ip():
    # Сначала без Tor
    try:
        normal_ip = requests.get('https://api.ipify.org', timeout=5).text
        print(f"Мой реальный IP: {normal_ip}")
    except:
        print("Не могу получить реальный IP")

    # Через Tor
    proxies = {
        'http': 'socks5://localhost:9050',
        'https': 'socks5://localhost:9050'
    }
    
    try:
        tor_ip = requests.get('https://api.ipify.org', proxies=proxies, timeout=10).text
        print(f"Мой IP через Tor: {tor_ip}")
    except Exception as e:
        print(f"Не могу подключиться через Tor: {e}")
        print("Убедитесь что Tor установлен: sudo apt install tor")

# Основной скрипт
def main():
    print("=== Простой Tor скрипт ===\n")
    
    # Запускаем Tor
    if start_tor():
        # Проверяем IP
        print("\nПроверяем IP-адреса...")
        check_ip()
    else:
        print("\nНе удалось запустить Tor")

if __name__ == "__main__":
    main()