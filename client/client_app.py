import asyncio
import json
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import pygame
import websockets

# ===== 接続先 =====
WS_URL = "wss://rng-alert.onrender.com/ws"

# ===== 設定ファイル =====
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "client_config.json"
DEFAULT_SOUND_PATH = BASE_DIR / "default_alarm.mp3"   # ここにデフォルト音を置く

# ===== 状態 =====
alarm_running = False
loop = None


def ensure_audio_initialized():
    """pygame mixer を初期化"""
    if not pygame.mixer.get_init():
        pygame.mixer.init()


def load_config():
    """設定ファイル読み込み。無ければデフォルト設定を返す"""
    default_config = {
        "sound_path": str(DEFAULT_SOUND_PATH),
        "volume": 1.0,
    }

    if not CONFIG_PATH.exists():
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "sound_path" not in data:
            data["sound_path"] = str(DEFAULT_SOUND_PATH)
        if "volume" not in data:
            data["volume"] = 1.0

        return data
    except Exception as e:
        print("config load error:", e)
        return default_config


def save_config():
    """現在の設定を保存"""
    try:
        config = {
            "sound_path": sound_path_var.get(),
            "volume": volume_var.get(),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        status_var.set("設定を保存しました")
    except Exception as e:
        messagebox.showerror("保存エラー", f"設定の保存に失敗しました:\n{e}")


def validate_sound_file(path_str: str) -> bool:
    """音声ファイルの存在と拡張子を確認"""
    if not path_str:
        return False

    path = Path(path_str)
    if not path.exists():
        return False

    return path.suffix.lower() in {".mp3", ".wav"}


def play_selected_sound(loop_play: bool):
    """選択中の音声を再生"""
    sound_path = sound_path_var.get().strip()

    if not validate_sound_file(sound_path):
        messagebox.showwarning(
            "音声ファイルエラー",
            "音声ファイルが見つからないか、mp3 / wav ではありません。"
        )
        return False

    try:
        ensure_audio_initialized()
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.set_volume(volume_var.get())

        # loop_play=True なら無限ループ
        pygame.mixer.music.play(-1 if loop_play else 0)
        return True
    except Exception as e:
        messagebox.showerror("再生エラー", f"音声の再生に失敗しました:\n{e}")
        return False


def start_alarm():
    """アラーム開始"""
    global alarm_running
    if alarm_running:
        return

    if play_selected_sound(loop_play=True):
        alarm_running = True
        status_var.set("🚨 ALARM")


def stop_alarm():
    """アラーム停止"""
    global alarm_running
    alarm_running = False
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception as e:
        print("stop sound error:", e)

    status_var.set("待機中")


def test_sound():
    """テスト再生"""
    stop_alarm()
    ok = play_selected_sound(loop_play=False)
    if ok:
        status_var.set("テスト再生中")


def choose_sound_file():
    """ファイル選択"""
    selected = filedialog.askopenfilename(
        title="アラーム音を選択",
        filetypes=[
            ("音声ファイル", "*.mp3 *.wav"),
            ("MP3 ファイル", "*.mp3"),
            ("WAV ファイル", "*.wav"),
            ("すべてのファイル", "*.*"),
        ],
    )

    if selected:
        sound_path_var.set(selected)
        status_var.set("音声ファイルを変更しました")


def set_default_sound():
    """デフォルト音に戻す"""
    sound_path_var.set(str(DEFAULT_SOUND_PATH))
    status_var.set("デフォルト音に戻しました")


async def ws_main():
    while True:
        try:
            root.after(0, lambda: status_var.set("接続中..."))
            async with websockets.connect(
                WS_URL,
                ping_interval=20,
                ping_timeout=10,
            ) as ws:
                print("ws connected")
                root.after(0, lambda: status_var.set("接続中"))

                while True:
                    message = await ws.recv()
                    print("message:", message)
                    data = json.loads(message)
                    if data.get("type") == "alarm":
                        root.after(0, start_alarm)

        except Exception as e:
            print("ws error:", e)
            root.after(0, lambda: status_var.set("再接続中"))
            await asyncio.sleep(5)


def run_async_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_main())


# ===== GUI =====
config = load_config()

root = tk.Tk()
root.title("Alarm Client")
root.geometry("520x400")

status_var = tk.StringVar(value="起動中")
sound_path_var = tk.StringVar(value=config["sound_path"])
volume_var = tk.DoubleVar(value=config["volume"])

title_label = tk.Label(root, text="Alarm Client", font=("Yu Gothic UI", 18, "bold"))
title_label.pack(pady=(12, 8))

status_label = tk.Label(root, textvariable=status_var, font=("Yu Gothic UI", 14))
status_label.pack(pady=(0, 12))

sound_frame = tk.Frame(root)
sound_frame.pack(fill="x", padx=12)

tk.Label(sound_frame, text="アラーム音:", font=("Yu Gothic UI", 11)).pack(anchor="w")
sound_entry = tk.Entry(sound_frame, textvariable=sound_path_var, font=("Yu Gothic UI", 10))
sound_entry.pack(fill="x", pady=(4, 8))

button_frame1 = tk.Frame(root)
button_frame1.pack(fill="x", padx=12, pady=(0, 8))

choose_button = tk.Button(
    button_frame1,
    text="音声ファイルを選ぶ",
    font=("Yu Gothic UI", 11),
    command=choose_sound_file,
)
choose_button.pack(side="left", padx=(0, 8))

default_button = tk.Button(
    button_frame1,
    text="デフォルト音に戻す",
    font=("Yu Gothic UI", 11),
    command=set_default_sound,
)
default_button.pack(side="left")

volume_frame = tk.Frame(root)
volume_frame.pack(fill="x", padx=12, pady=(0, 8))

tk.Label(volume_frame, text="音量:", font=("Yu Gothic UI", 11)).pack(anchor="w")
volume_scale = tk.Scale(
    volume_frame,
    from_=0.0,
    to=1.0,
    resolution=0.1,
    orient="horizontal",
    variable=volume_var,
    length=300,
)
volume_scale.pack(anchor="w")

button_frame2 = tk.Frame(root)
button_frame2.pack(fill="x", padx=12, pady=(8, 8))

test_button = tk.Button(
    button_frame2,
    text="テスト再生",
    font=("Yu Gothic UI", 12),
    command=test_sound,
    width=12,
)
test_button.pack(side="left", padx=(0, 8))

stop_button = tk.Button(
    button_frame2,
    text="停止",
    font=("Yu Gothic UI", 12),
    command=stop_alarm,
    width=12,
)
stop_button.pack(side="left", padx=(0, 8))

save_button = tk.Button(
    button_frame2,
    text="設定を保存",
    font=("Yu Gothic UI", 12),
    command=save_config,
    width=12,
)
save_button.pack(side="left")

info_label = tk.Label(
    root,
    text="mp3 / wav を指定できます。設定は client_config.json に保存されます。",
    font=("Yu Gothic UI", 10),
)
info_label.pack(pady=(12, 8))

threading.Thread(target=run_async_loop, daemon=True).start()

root.mainloop()