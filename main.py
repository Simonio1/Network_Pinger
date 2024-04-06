import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import tkinter.messagebox as msgbox
import threading
import time
import subprocess
import json
import winsound
import sys
import os


def show_ip_tooltip(event, ip):
    # Check if there's already a tooltip window and destroy it
    if hasattr(show_ip_tooltip, 'tooltip'):
        show_ip_tooltip.tooltip.destroy()

    tooltip = tk.Toplevel(bg='white', padx=1, pady=1)
    tooltip.overrideredirect(True)
    x = event.widget.winfo_rootx() + 20
    y = event.widget.winfo_rooty() + 20
    tooltip.geometry(f"+{x}+{y}")
    tk.Label(tooltip, text="IP : "+ip, bg='white').pack()

    # Store the tooltip window in the function's attribute for later access
    show_ip_tooltip.tooltip = tooltip

    # Ensure the tooltip is destroyed when the mouse leaves the label
    def on_leave(e):
        if hasattr(show_ip_tooltip, 'tooltip'):
            show_ip_tooltip.tooltip.destroy()
            delattr(show_ip_tooltip, 'tooltip')  # Remove the attribute to avoid reference issues

    # Bind the leave event to the label
    event.widget.bind('<Leave>', on_leave)

def load_devices_from_json(file_path):
    with open(file_path, 'r') as file:
        devices = json.load(file)
        for device in devices:
            device.setdefault("FailedPings", 0)  # Initialize FailedPings as integer if not present
        return devices

def save_devices_to_json(file_path, devices):
    with open(file_path, 'w') as file:
        json.dump(devices, file, indent=4)

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def add_device():
    name = simpledialog.askstring("Add Device", "Enter device name:")
    if not name:
        return
    ip = simpledialog.askstring("Add Device", "Enter device IP:")
    if not ip:
        return
    site = simpledialog.askstring("Add Device", "Enter device location:")
    if not site:
        return
    new_device = {'name': name, 'IP': ip, 'Site': site, 'Status': "Initializing", 'Time': time.strftime("%H:%M:%S"), 'FailedPings': 0}
    devices.append(new_device)
    save_devices_to_json("devices.json", devices)
    restart_program()

def remove_device():
    def delete_selected_device():
        selected_device = device_listbox.get(device_listbox.curselection())
        for device in devices:
            if device['name'] == selected_device:
                devices.remove(device)
                break
        save_devices_to_json("devices.json", devices)
        restart_program()

    device_list = [device['name'] for device in devices]
    if not device_list:
        messagebox.showinfo("Remove Device", "No devices to remove.")
        return

    remove_window = tk.Toplevel(root)
    remove_window.title("Remove Device")

    tk.Label(remove_window, text="Select device to remove:").pack()
    device_listbox = tk.Listbox(remove_window, selectmode=tk.SINGLE)
    for device in device_list:
        device_listbox.insert(tk.END, device)
    device_listbox.pack()

    remove_button = tk.Button(remove_window, text="Remove", command=delete_selected_device)
    remove_button.pack()

if os.path.exists('devices.JSON'):
    devices = load_devices_from_json("devices.json")
    ping_timeout = 1000
    retry_count = 3
else:
    data = []
    with open('devices.JSON', 'w') as file:
        json.dump(data, file, indent=6)
    devices = load_devices_from_json("devices.json")
    ping_timeout = 1000
    retry_count = 3

def ping_device(ip):
    try:
        response = subprocess.run(['ping', '-n', '1', '-w', str(ping_timeout), ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return "TTL=" in response.stdout.decode()
    except Exception as e:
        update_status(f"Error pinging {ip}: {e}")
        return False

def update_device_status():
    # Periodically update the device status
    while True:
        update_status("Starting device scan...")
        for device in devices:
            previous_status = device.get("Status", "UP")
            status = ping_device(device["IP"])
            if "FailedPings" not in device:
                device["FailedPings"] = 0
            if status:
                device["Status"] = "UP"
                device["FailedPings"] = 0
            else:
                device["FailedPings"] += 1
                if device["FailedPings"] < retry_count:
                    device["Status"] = "NON RESPONSIVE"
                else:
                    device["Status"] = "DOWN"
            if previous_status != "DOWN" and device["Status"] == "DOWN":
                show_warning_message(device['name'], device['Site'])
            device["Time"] = time.strftime("%d-%m-%Y , %H:%M:%S")
            label_text = f"{device['name']} is {device['Status']} - {device['Time']}"
            if device["Status"] == "UP":
                color = '#00FF00'
            elif device["Status"] == "NON RESPONSIVE":
                color = '#FFFF00'
            else:
                color = '#FF0000'
            device_labels[(device['name'], device['Site'])].config(text=label_text, bg=color, fg='black')
        update_status("Device scan completed.")
        interval = scan_interval.get()
        for i in range(interval, 0, -1):
            countdown_label.config(text=f"Next scan in: {i} seconds")
            time.sleep(1)


def show_warning_message(device_name, location):
    message = f"The device '{device_name}' at '{location}' is now DOWN."
    top = tk.Toplevel(root)
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()
    top.geometry(f"{screen_width//2}x{screen_height//2}+{screen_width//4}+{screen_height//4}")
    top.configure(bg='red')
    top.attributes('-topmost', True)
    msg = tk.Label(top, text=message, bg='red', fg='white', font=('Courier', 20))
    msg.pack(expand=True, fill='both')
    def close_msgbox():
        top.destroy()
    root.after(10000, close_msgbox)
    play_warning_sound()

def play_warning_sound():
    for _ in range(3):
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        time.sleep(1)

def update_status(message):
    status_bar.config(text=message)
    status_bar.pack(side=tk.TOP, pady=5)
    status_bar.config(bg='#333333', fg='white')

def show_about():
    msgbox.showinfo("About", "גרסה 1.2 ,נוצר על ידי סיימון בנג'מין ולבי, ליצירת קשר  053-722-7573")

def create_gui():
    global root, site_frames, device_labels, countdown_label, scan_interval, status_bar
    root = tk.Tk()
    root.title("Network Device Monitor")
    root.configure(bg='#333333')




    site_frames = {}
    device_labels = {}

    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=file_menu)
    file_menu.add_command(label="Add Device", command=add_device)
    file_menu.add_command(label="Remove Device", command=remove_device)
    file_menu.add_command(label="About", command=show_about)



    for device in devices:
        site = device['Site']
        if site not in site_frames:
            frame = tk.Frame(root, bg='#333333', pady=5)
            frame.pack( padx=20, pady=10, fill='x', expand=True)
            tk.Label(frame, text=site, bg='#333333', fg='white', font='Courier 14 bold').pack(fill='x')
            site_frames[site] = frame
        else:
            frame = site_frames[site]

        label_text = f"{device['name']} is {device['Status']} - {device['Time']}"
        label = tk.Label(frame, text=label_text, bg='#333333', fg='white', font='Courier 12')
        label.pack(pady=2, padx=10, fill='x')
        device_labels[(device['name'], site)] = label
        label.bind("<Enter>", lambda e, ip=device['IP']: show_ip_tooltip(e, ip))





    interval_frame = tk.Frame(root, bg='#333333')
    interval_frame.pack(side=tk.TOP, pady=5)

    interval_label = tk.Label(interval_frame, text="Select Scan Duration:", bg='#333333', fg='white')
    interval_label.pack(side=tk.LEFT, padx=10)

    scan_interval = tk.IntVar(value=15)
    interval_options = [15, 30, 60, 5 * 60]
    interval_combobox = ttk.Combobox(interval_frame, textvariable=scan_interval, values=interval_options, width=10, state='readonly')
    interval_combobox = interval_combobox.pack(side=tk.LEFT)

    countdown_label = tk.Label(root, text="Next scan in: 15 seconds", bg='#333333', fg='white')
    countdown_label.pack(side=tk.TOP)

    status_bar = tk.Label(root, bg='#333333', fg='white', anchor='center')
    status_bar.pack(side=tk.BOTTOM)

    root.resizable(False, False)

    def toggle_always_on_top():
        root.attributes('-topmost', var_always_on_top.get())

    var_always_on_top = tk.IntVar()
    checkbutton_always_on_top = tk.Checkbutton(root, text='Always on Top', variable=var_always_on_top, command=toggle_always_on_top, bg='#333333', fg='white', selectcolor='#4f591a', activebackground='#4f591a')
    checkbutton_always_on_top.pack(side=tk.TOP)

    def on_close():
        tk.messagebox.showinfo("אופציה בוטלה", "האופציה לסגירת האפליקצייה מבוטלת, יש לבצע הפעלה מחדש")
        pass

    root.protocol("WM_DELETE_WINDOW", on_close)

    threading.Thread(target=update_device_status, daemon=True).start()
    root.mainloop()

def save_and_restart(root):
    if messagebox.askyesno("Restart Required", "Changes have been saved. Restart application now?"):
        restart_program()

if __name__ == "__main__":
    create_gui()

