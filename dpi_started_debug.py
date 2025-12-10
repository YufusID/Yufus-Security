#!/usr/bin/env python3
import socket
import ssl
import threading

LOCAL_HOST = '127.0.0.1'
LOCAL_PORT = 8888

def handle_client(client_socket):
    try:
        request = client_socket.recv(4096)
        # Просто перенаправляем трафик
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect(('8.8.8.8', 443))  # или другой сервер
        remote_socket.send(request)
        
        while True:
            response = remote_socket.recv(4096)
            if not response:
                break
            client_socket.send(response)
    except:
        pass
    finally:
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LOCAL_HOST, LOCAL_PORT))
    server.listen(5)
    
    print(f" ✅ Успешно подключено к {LOCAL_HOST}:{LOCAL_PORT}")
    
    while True:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    main()