import pyperclip
import time
import threading
from datetime import datetime
import pyautogui
import tkinter as tk
import humanize
import queue


last_label = None

def show_tooltip(root, text, x, y):
    print(f"Showing tooltip: {text} at ({x}, {y})")
    global last_label

    if last_label is not None:
        last_label.master.destroy()  # destroy the previous tooltip
        last_label = None
        # last_label.destroy()
    if text == "not a valid date": # if not a valid date, just exit
        return
    tooltip = tk.Toplevel(root)
    # print(tooltip)

    tooltip.overrideredirect(True)  # removes window borders
    tooltip.attributes('-topmost', True)  # ensures tooltip stays above all windows
    tooltip.geometry(f"+{x}+{y}")
    label = tk.Label(tooltip, text=text, bg="lightblue")
    label.pack(expand=True)
    last_label = label

    label.config(font=("Helvetica", 15))  # set font size and type
    # set font color
    label.config(fg="black")  # set font color
    tooltip.attributes("-alpha", 0.9)  # set transparency level (0.0 to 1.0)

    # print("label:", label)

    def fade_out():
        alpha = tooltip.attributes("-alpha")
        if alpha > 0:
            tooltip.attributes("-alpha", alpha - 0.03)
            tooltip.after(25, fade_out)

    # follow the mouse
    def follow_mouse():
        x, y = pyautogui.position()
        tooltip.geometry(f"+{x+10}+{y-10}")
        tooltip.after(5, follow_mouse)

    follow_mouse()
    
    if text != "not a valid date":
        tooltip.after(20000, fade_out)  # start fading out
    else:
        tooltip.after(1000, fade_out)
    

def monitor_clipboard(tooltip_queue): # run in a separate thread
    print("Monitoring clipboard...")

    last_text = ""
    while True:
        try:
            current_text = pyperclip.paste().strip()  # Clean up whitespace
            if current_text != last_text:
                
                last_text = current_text

                # 1747560279331
                # 1747540943.0
                if current_text.isdigit() or (current_text.replace('.', '', 1).isdigit() and current_text.count('.') < 2):
                    epoch = float(current_text)
                    if 1000000000 < epoch < 9999999999:  # plausible range
                        date_str = datetime.fromtimestamp(epoch).strftime("%d %B %Y %I:%M %p")
                        relative_time = humanize.naturaltime(datetime.now() - datetime.fromtimestamp(epoch))
                        date_str += f" ({relative_time})"
                        
                        tooltip_queue.put((date_str, 0, 0))
                    elif 100000000000 < epoch < 9999999999999:  # plausible range
                        date_str = datetime.fromtimestamp(epoch / 1000).strftime("%d %B %Y %I:%M %p")
                        relative_time = humanize.naturaltime(datetime.now() - datetime.fromtimestamp(epoch / 1000))
                        date_str += f" ({relative_time})"
                        
                        tooltip_queue.put((date_str, 0, 0))
                    else:
                        tooltip_queue.put(("not a valid date", 0, 0))
                
                # 2025-05-18T16:33:14
                elif len(current_text) == 19 and current_text[4] == '-' and current_text[7] == '-' and current_text[10] == 'T' and current_text[13] == ':' and current_text[16] == ':':
                    # check if the text is a valid date
                    try:
                        date_str = datetime.fromisoformat(current_text).strftime("%d %B %Y %I:%M %p")
                        relative_time = humanize.naturaltime(datetime.now() - datetime.fromisoformat(current_text))
                        date_str += f" ({relative_time})"
                        
                        tooltip_queue.put((date_str, 0, 0))
                    except:
                        pass

                # 2022-10-05T16:00:00.000Z
                elif len(current_text) == 24 and current_text[4] == '-' and current_text[7] == '-' and current_text[10] == 'T' and current_text[13] == ':' and current_text[16] == ':' and current_text[19] == '.':
                    # check if the text is a valid date
                    try:
                        date_str = datetime.fromisoformat(current_text[:-1]).strftime("%d %B %Y %I:%M %p")
                        relative_time = humanize.naturaltime(datetime.now() - datetime.fromisoformat(current_text[:-1]))
                        date_str += f" ({relative_time})"
                        
                        tooltip_queue.put((date_str, 0, 0))
                    except:
                        pass

                # 2022-10-05T12:00:00-04:00
                elif len(current_text) == 25 and current_text[4] == '-' and current_text[7] == '-' and current_text[10] == 'T' and current_text[13] == ':' and current_text[16] == ':' and current_text[19] == '-':
                    # check if the text is a valid date
                    try:
                        date_str = datetime.fromisoformat(current_text).strftime("%d %B %Y %I:%M %p")
                        # convert to epoch
                        epoch = datetime.fromisoformat(current_text).timestamp()
                        relative_time = humanize.naturaltime(datetime.now() - datetime.fromtimestamp(epoch))
                        date_str += f" ({relative_time})"
                        
                        tooltip_queue.put((date_str, 0, 0))
                    except Exception as e:
                        print("Error parsing date:", e)
                        tooltip_queue.put(("not a valid date", 0, 0))
                        

                else:
                    tooltip_queue.put(("not a valid date", 0, 0))

                

        except Exception as e:
            print("Error accessing clipboard:", e)
            tooltip_queue.put(("not a valid date", 0, 0))
        time.sleep(0.5)  # polling delay

def main():
    tooltip_queue = queue.Queue()

    def process_queue():
        try:
            while not tooltip_queue.empty():
                text, x, y = tooltip_queue.get_nowait()
                show_tooltip(root, text, x, y) # under the main thread, render the tooltip with new text
        except queue.Empty:
            pass
        root.after(100, process_queue)

    # Create a hidden Tkinter window in the main thread
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    root.attributes('-topmost', True)  # Keep the main window on top
    root.geometry("1x1")  # Set a small size for the main window
    root.overrideredirect(True)  # Remove window borders
    root.attributes("-alpha", 0.0)  # Make the main window invisible

    # Start the clipboard monitoring thread
    threading.Thread(target=monitor_clipboard, args=(tooltip_queue,), daemon=True).start()


    process_queue() # Start polling the queue for new tooltips
    # Start the Tkinter main loop, which will keep the application running
    root.mainloop()

if __name__ == "__main__":
    main()