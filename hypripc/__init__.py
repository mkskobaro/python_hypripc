import os
import select
import socket
import subprocess


class Listener:
    def __init__(self, event: bytes, callback: callable, process_all: bool = False):
        self.event = event
        self.callback = callback
        self.process_all = process_all


def write_socket_filename() -> str:
    hyprland_signature = os.getenv('HYPRLAND_INSTANCE_SIGNATURE')
    xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR')
    hyprland_command_put_socket_filename = f'{xdg_runtime_dir}/hypr/{hyprland_signature}/.socket.sock'
    return hyprland_command_put_socket_filename


def read_socket_filename() -> str:
    hyprland_signature = os.getenv('HYPRLAND_INSTANCE_SIGNATURE')
    xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR')
    hyprland_events_read_socket_filename = f'{xdg_runtime_dir}/hypr/{hyprland_signature}/.socket2.sock'
    return hyprland_events_read_socket_filename


def cmd_sock(command: str) -> str or None:
    command = f'j/{command}'
    result = b''
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as ws:
        ws.connect(write_socket_filename())
        ws.send(command.encode())
        while True:
            data = ws.recv(8192)
            if not data:
                break
            result += data
        match result:
            case b'ok':
                return None
            case b'unknown request' | b'invalid command':
                raise Exception(f'Unknown request: {command}')
            case _:
                return result.decode()


def cmd_ctl(command: str) -> str or None:
    command = command.split()
    command.insert(0, '-j')
    command.insert(0, 'hyprctl')
    stdout = subprocess.run(command, capture_output=True, text=True, check=True).stdout
    match stdout:
        case 'ok\n':
            return None
        case 'unknown request\n' | 'invalid command\n':
            raise Exception(f'Unknown request: {command}')
        case _:
            return stdout


def loop(listeners: list[Listener]):
    event_to_listeners = {}
    for listener in listeners:
        if listener.event not in event_to_listeners:
            event_to_listeners[listener.event] = []
        event_to_listeners[listener.event].append(listener)
    always_listen_all = any(listener.process_all for listener in listeners)
    unprocessed_data = b''
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as rs:
        rs.connect(read_socket_filename())
        rs.setblocking(False)
        event_to_listeners_copy = event_to_listeners.copy() if always_listen_all else None
        while True:
            rsl, *_ = select.select([rs], [], [])
            if rs in rsl:
                data = rs.recv(4096)
                if not data:
                    raise Exception(f'Hyprland disconnected')
                unprocessed_data += data
            if len(unprocessed_data) > 0:
                lines = unprocessed_data.split(b'\n')
                unprocessed_data = lines.pop()
                for line in reversed(lines):
                    event, data = line.split(b'>>')
                    listeners = event_to_listeners_copy.pop(event, None) if always_listen_all else event_to_listeners.get(event)
                    if listeners is not None:
                        for listener in listeners:
                            listener.callback(data.decode())


def one_time(listener: Listener):
    unprocessed_data = b''
    while True:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as rs:
            rs.connect(read_socket_filename())
            rs.setblocking(False)
            while True:
                rsl, *_ = select.select([rs], [], [])
                if rs in rsl:
                    data = rs.recv(4096)
                    if not data:
                        raise Exception(f'Hyprland disconnected')
                    unprocessed_data += data
                if len(unprocessed_data) > 0:
                    lines = unprocessed_data.split(b'\n')
                    unprocessed_data = lines.pop()
                    for line in reversed(lines):
                        event, data = line.split(b'>>')
                        if event == listener.event:
                            listener.callback(data.decode())
                            return
