#!/usr/bin/env python3
"""
Скрипт для повышения приватности Bluetooth на Android
Требует root-доступ для некоторых функций
"""

import os
import sys
import random
import subprocess
import time
import sqlite3
from datetime import datetime
import logging
from typing import Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BluetoothPrivacy:
    def __init__(self, use_root: bool = False):
        self.use_root = use_root
        self.original_mac = None
        
    def check_root(self) -> bool:
        """Проверка наличия root-прав"""
        if os.geteuid() == 0:
            return True
        try:
            result = subprocess.run(['su', '-c', 'id'], 
                                  capture_output=True, text=True)
            return 'uid=0' in result.stdout
        except:
            return False
    
    def get_current_mac(self) -> Optional[str]:
        """Получение текущего MAC-адреса Bluetooth"""
        try:
            if os.path.exists('/sys/class/bluetooth/hci0/address'):
                with open('/sys/class/bluetooth/hci0/address', 'r') as f:
                    return f.read().strip()
        except Exception as e:
            logger.error(f"Ошибка получения MAC: {e}")
        return None
    
    def generate_random_mac(self) -> str:
        """Генерация случайного MAC-адреса"""
        # Локально администрируемый адрес (второй бит первого байта = 1)
        first_byte = random.randint(0x02, 0xFE) & 0xFE | 0x02
        mac = [first_byte]
        mac.extend(random.randint(0x00, 0xFF) for _ in range(5))
        return ':'.join(f'{b:02X}' for b in mac)
    
    def change_mac_address(self, new_mac: str = None) -> bool:
        """Смена MAC-адреса Bluetooth"""
        if not new_mac:
            new_mac = self.generate_random_mac()
        
        logger.info(f"Попытка смены MAC на: {new_mac}")
        
        # Сохраняем оригинальный MAC
        self.original_mac = self.get_current_mac()
        
        if not self.check_root():
            logger.error("Требуются root-права!")
            return False
        
        try:
            # Отключаем Bluetooth перед сменой MAC
            self.toggle_bluetooth(False)
            time.sleep(2)
            
            # Меняем MAC адрес
            commands = [
                f'echo "{new_mac}" > /sys/class/bluetooth/hci0/address',
                'service call bluetooth_manager 6',  # Остановка службы
                'service call bluetooth_manager 8',  # Отключение
                f'settings put secure bluetooth_address_override {new_mac}',
            ]
            
            for cmd in commands:
                subprocess.run(['su', '-c', cmd], 
                             capture_output=True, text=True)
            
            time.sleep(3)
            self.toggle_bluetooth(True)
            
            # Проверяем результат
            current_mac = self.get_current_mac()
            if current_mac and current_mac.upper() == new_mac.upper():
                logger.info(f"MAC успешно изменен: {current_mac}")
                return True
            else:
                logger.warning(f"MAC возможно не изменился. Текущий: {current_mac}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка смены MAC: {e}")
            return False
    
    def toggle_bluetooth(self, enable: bool) -> bool:
        """Включение/выключение Bluetooth"""
        try:
            state = 'enable' if enable else 'disable'
            cmd = ['su', '-c', f'service call bluetooth_manager {6 if enable else 8}']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Альтернативный метод через am
            am_cmd = ['su', '-c', 
                     f'am start -a android.bluetooth.adapter.action.{state.upper()}_BLE']
            subprocess.run(am_cmd, capture_output=True, text=True)
            
            logger.info(f"Bluetooth {'включен' if enable else 'выключен'}")
            return True
        except Exception as e:
            logger.error(f"Ошибка управления Bluetooth: {e}")
            return False
    
    def set_bluetooth_visibility(self, visible: bool) -> bool:
        """Настройка видимости Bluetooth"""
        try:
            value = 120 if visible else 0  # 0 = невидимый, 1-120 = секунды видимости
            cmd = f'settings put global bluetooth_discoverable_timeout {value}'
            
            if self.use_root:
                subprocess.run(['su', '-c', cmd], capture_output=True, text=True)
            else:
                subprocess.run(['adb', 'shell', cmd], capture_output=True, text=True)
            
            logger.info(f"Видимость Bluetooth: {'включена' if visible else 'выключена'}")
            return True
        except Exception as e:
            logger.error(f"Ошибка настройки видимости: {e}")
            return False
    
    def clear_paired_devices(self) -> bool:
        """Очистка списка сопряженных устройств"""
        try:
            if self.check_root():
                commands = [
                    'rm -f /data/misc/bluedroid/bt_config*',
                    'rm -f /data/misc/bluetooth/bt_config*',
                    'pm clear com.android.bluetooth',
                ]
                
                for cmd in commands:
                    subprocess.run(['su', '-c', cmd], 
                                 capture_output=True, text=True)
                
                logger.info("Список сопряженных устройств очищен")
                return True
        except Exception as e:
            logger.error(f"Ошибка очистки устройств: {e}")
        
        return False
    
    def disable_bluetooth_services(self) -> bool:
        """Отключение Bluetooth сервисов"""
        try:
            services = [
                'com.android.bluetooth',
                'com.android.bluetoothmidiservice',
                'com.android.bluetooth.opp',
                'com.android.bluetooth.pbap',
            ]
            
            for service in services:
                cmd = f'pm disable-user {service}'
                subprocess.run(['su', '-c', cmd], capture_output=True, text=True)
            
            logger.info("Bluetooth сервисы отключены")
            return True
        except Exception as e:
            logger.error(f"Ошибка отключения сервисов: {e}")
            return False
    
    def spoof_bluetooth_name(self, new_name: str = "Unknown Device") -> bool:
        """Изменение имени Bluetooth устройства"""
        try:
            cmd = f'settings put global bluetooth_name "{new_name}"'
            
            if self.use_root:
                subprocess.run(['su', '-c', cmd], capture_output=True, text=True)
            else:
                subprocess.run(['adb', 'shell', cmd], capture_output=True, text=True)
            
            logger.info(f"Имя Bluetooth изменено на: {new_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка смены имени: {e}")
            return False
    
    def monitor_bluetooth_activity(self, duration: int = 300) -> None:
        """Мониторинг Bluetooth активности"""
        logger.info(f"Начало мониторинга Bluetooth на {duration} секунд")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                # Проверка состояния Bluetooth
                result = subprocess.run(
                    ['su', '-c', 'dumpsys bluetooth_manager'],
                    capture_output=True, text=True
                )
                
                if 'enabled: true' in result.stdout:
                    logger.warning("Bluetooth включен!")
                
                # Поиск активных соединений
                if 'CONNECTED' in result.stdout:
                    logger.warning("Обнаружено активное соединение!")
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
    
    def restore_original_mac(self) -> bool:
        """Восстановление оригинального MAC-адреса"""
        if self.original_mac:
            logger.info(f"Восстановление оригинального MAC: {self.original_mac}")
            return self.change_mac_address(self.original_mac)
        return False
    
    def get_bluetooth_info(self) -> dict:
        """Получение информации о Bluetooth"""
        info = {
            'current_mac': self.get_current_mac(),
            'original_mac': self.original_mac,
            'bluetooth_name': None,
            'visibility': None,
        }
        
        try:
            # Получение имени устройства
            result = subprocess.run(
                ['su', '-c', 'settings get global bluetooth_name'],
                capture_output=True, text=True
            )
            info['bluetooth_name'] = result.stdout.strip()
            
            # Получение настроек видимости
            result = subprocess.run(
                ['su', '-c', 'settings get global bluetooth_discoverable_timeout'],
                capture_output=True, text=True
            )
            info['visibility'] = result.stdout.strip()
            
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
        
        return info


def display_menu():
    """Отображение меню"""
    print("\n" + "="*50)
    print("Bluetooth Privacy Manager")
    print("="*50)
    print("1. Сменить MAC-адрес")
    print("2. Выключить видимость Bluetooth")
    print("3. Очистить сопряженные устройства")
    print("4. Выключить Bluetooth сервисы")
    print("5. Изменить имя устройства")
    print("6. Получить информацию")
    print("7. Мониторинг активности")
    print("8. Восстановить оригинальный MAC")
    print("9. Комплексная защита")
    print("0. Выход")
    print("="*50)
    return input("Выберите действие: ").strip()


def main():
    """Основная функция"""
    print("Инициализация Bluetooth Privacy Manager...")
    
    # Проверка платформы
    if sys.platform != 'linux':
        print("Внимание: Скрипт предназначен для Android/Linux")
    
    # Создание экземпляра
    privacy = BluetoothPrivacy(use_root=True)
    
    if not privacy.check_root():
        print("Предупреждение: Root-права не обнаружены!")
        print("Некоторые функции могут быть недоступны")
        response = input("Продолжить? (y/n): ")
        if response.lower() != 'y':
            return
    
    while True:
        choice = display_menu()
        
        if choice == '1':
            # Смена MAC-адреса
            print("\n--- Смена MAC-адреса ---")
            custom_mac = input("Введите свой MAC (Enter для случайного): ").strip()
            if custom_mac:
                privacy.change_mac_address(custom_mac)
            else:
                privacy.change_mac_address()
            
        elif choice == '2':
            # Выключение видимости
            print("\n--- Настройка видимости ---")
            privacy.set_bluetooth_visibility(False)
            print("Режим невидимости активирован")
            
        elif choice == '3':
            # Очистка устройств
            print("\n--- Очистка сопряженных устройств ---")
            if privacy.clear_paired_devices():
                print("Устройства очищены")
            else:
                print("Ошибка очистки")
                
        elif choice == '4':
            # Отключение сервисов
            print("\n--- Отключение Bluetooth сервисов ---")
            if privacy.disable_bluetooth_services():
                print("Сервисы отключены")
            else:
                print("Ошибка отключения")
                
        elif choice == '5':
            # Изменение имени
            print("\n--- Изменение имени устройства ---")
            new_name = input("Введите новое имя: ").strip()
            if new_name:
                privacy.spoof_bluetooth_name(new_name)
                
        elif choice == '6':
            # Информация
            print("\n--- Информация о Bluetooth ---")
            info = privacy.get_bluetooth_info()
            for key, value in info.items():
                print(f"{key}: {value}")
                
        elif choice == '7':
            # Мониторинг
            print("\n--- Мониторинг активности ---")
            try:
                duration = int(input("Длительность (секунды): "))
                privacy.monitor_bluetooth_activity(duration)
            except ValueError:
                print("Неверный ввод")
                
        elif choice == '8':
            # Восстановление MAC
            print("\n--- Восстановление MAC ---")
            if privacy.restore_original_mac():
                print("MAC восстановлен")
            else:
                print("Оригинальный MAC не найден")
                
        elif choice == '9':
            # Комплексная защита
            print("\n--- Комплексная защита ---")
            print("Выполняются все меры защиты...")
            
            privacy.toggle_bluetooth(False)
            time.sleep(2)
            
            privacy.change_mac_address()
            privacy.set_bluetooth_visibility(False)
            privacy.spoof_bluetooth_name("Private Device")
            privacy.clear_paired_devices()
            privacy.disable_bluetooth_services()
            
            print("Все меры защиты применены!")
            
        elif choice == '0':
            # Выход
            print("\nВыход...")
            break
            
        else:
            print("\nНеверный выбор!")
        
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nСкрипт прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")