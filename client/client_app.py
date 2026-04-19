import threading
import tkinter as tk
import websocket
import json
import winsound
import time

# RenderのURLに書き換えてください
WS_URL = "wss://rng-alert.onrender.com//ws"

alarm_running = False

def play_alarm():
    global alarm_running
    while alarm_running:
        try:
            winsound.Beep(2000, 800)
            time.sleep(0.2)
        except Exception as e:
            print("sound error:", e)
            time.sleep(1)

def start_alarm():
    global alarm_running
    if alarm_running:
        return
    alarm_running = True
    status_var.set("🚨 ALARM")
    threading.Thread(target=play_alarm, daemon=True).start()

def stop_alarm():
    global alarm_running
    alarm_running = False
    status_var.set("待機中")

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "alarm":
            root.after(0, start_alarm)
    except Exception as e:
        print("message error:", e)

def on_error(ws, error):
    print("ws error:", error)
    root.after(0, lambda: status_var.set("接続エラー"))

def on_close(ws, close_status_code, close_msg):
    print("ws closed")
    root.after(0, lambda: status_var.set("切断"))

def on_open(ws):
    print("ws connected")
    root.after(0, lambda: status_var.set("接続中"))

def ws_loop():
    while True:
        try:
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            print("run_forever error:", e)

        root.after(0, lambda: status_var.set("再接続中"))
        time.sleep(5)

root = tk.Tk()
root.title("Alarm Client")
root.geometry("320x180")

status_var = tk.StringVar(value="起動中")

label = tk.Label(root, textvariable=status_var, font=("Yu Gothic UI", 18))
label.pack(pady=20)

stop_button = tk.Button(root, text="停止", font=("Yu Gothic UI", 16), command=stop_alarm)
stop_button.pack(pady=10)

threading.Thread(target=ws_loop, daemon=True).start()

root.mainloop()