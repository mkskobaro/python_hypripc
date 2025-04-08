#!/usr/bin/env python
import os.path
import random

import hypripc


def get_wallpapers_dir() -> str:
    wallpaper_dir = os.getenv('XDG_CONFIG_HOME')
    if not wallpaper_dir:
        wallpaper_dir = os.path.expanduser('~/.config')
    wallpaper_dir = os.path.join(wallpaper_dir, 'wallpapers')
    return wallpaper_dir


def get_wallpapers() -> list[str]:
    wallpaper_dir = get_wallpapers_dir()
    return [w for w in os.listdir(wallpaper_dir) if w.endswith(('.png', '.jpg', '.jpeg'))]


def get_monitor_to_active_wallpaper() -> dict[str, str | None]:
    monitors = [m['name'] for m in hypripc.get_monitors()]
    monitor_to_wallpaper = {m: None for m in monitors}
    active_wallpapers = [aw for aw in hypripc.cmd_ctl('hyprpaper listactive').split('\n') if aw]
    if active_wallpapers[0] != 'no wallpapers active':
        for r in active_wallpapers:
            if not r:
                continue
            monitor, wallpaper = r.split(' = ')
            if not monitor:
                continue
            monitor_to_wallpaper[monitor] = os.path.basename(wallpaper)
    return monitor_to_wallpaper


def set_random_wallpaper():
    wallpapers = get_wallpapers()
    active_wallpapers = get_monitor_to_active_wallpaper()
    for monitor, wallpaper in active_wallpapers.items():
        wallpapers_copy = wallpapers.copy()
        if wallpaper in wallpapers_copy:
            wallpapers_copy.remove(wallpaper)
        new_wallpaper = wallpapers_copy[random.randint(0, len(wallpapers_copy) - 1)]
        new_wallpaper = os.path.join(get_wallpapers_dir(), new_wallpaper)
        hypripc.cmd_ctl(f'hyprpaper reload {monitor},{new_wallpaper}')
        print(f'Set wallpaper for {monitor} to {new_wallpaper}')


set_random_wallpaper()
