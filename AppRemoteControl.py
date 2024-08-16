import keyboard
import cv2
from pynput import mouse
import pyautogui
import socket
from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageGrab, ImageTk, Image
import io
import time
from threading import Thread
import numpy
import pygetwindow as gw


class RemoteDesktop():
    def __init__(self, root):
        """
        Init function.

        Parameters
        ----------
        root : Tk
            The root of the tkinter window

        Returns
        -------
        None
        """
        self.root = root
        self.root.title("Remote Desktop")

        # Set remote control var
        self.run = False
        self.window = None

        # Set remote control var
        self.server_socket = None
        self.server_host = None
        self.server_port = 7850
        self.screenWidth, self.screenHeight = pyautogui.size()

        # Set instruction
        self.label1 = ttk.Label(root, text="Your IP : ")
        self.label1.pack(pady=10)

        # Set file path var
        self.user_ip = tk.StringVar()
        self.user_ip.set(self.get_internal_ip())# socket.gethostbyname(socket.gethostname())
        self.user_ip_entry = ttk.Entry(root, textvariable=self.user_ip, state="readonly")
        self.user_ip_entry.pack(pady=10, ipadx=100)

        # Set instruction
        self.label2 = ttk.Label(root, text="Enter the internal IP of the computer : ")
        self.label2.pack(pady=10)

        # Set field to enter a number for file number
        self.internal_ip = tk.StringVar()
        self.internal_ip_entry = ttk.Entry(root, textvariable=self.internal_ip)
        self.internal_ip_entry.pack(pady=10, ipadx=100)

        # Set button to start upload file
        self.start_button = ttk.Button(root, text="Start", command=lambda: self.start_remote())
        self.start_button.pack(pady=10)

        # Set button to start upload file
        self.stop_button = ttk.Button(root, text="Stop", command=lambda: self.stop_remote())
        self.stop_button.pack(pady=10)

        # Set lable
        self.status_label = ttk.Label(root, text="System status :")
        self.status_label.pack(pady=10)

        # Set area for status for every file
        self.text_status = tk.Text(root, height=20, width=100, state="disabled", background="black")
        self.text_status.pack(pady=10)
        self.text_status.tag_configure("defult", foreground="white")
        self.text_status.tag_configure("title", foreground="green")
        self.text_status.tag_configure("action", foreground="blue")
        self.text_status.tag_configure("warning", foreground="red")

        # Set quit button
        self.quit_button = ttk.Button(root, text="Quit", command=lambda: root.quit)
        self.quit_button.pack(pady=10)

        self.WriteOnScreen("The system was activated successfully", "defult")

    def get_internal_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None

    def start_server_request(self):
        """
        The function create a server for remote control who wants taking over him.
        If someone want to control his computer, a request will show and than the remote will start.

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        if not self.server_socket == None:
            self.server_socket.close()
            self.server_socket = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.user_ip.get(), self.server_port))
        self.server_socket.listen(1)
        print(f"Server listen to {self.user_ip.get()} : {self.server_port}")
        
        screenshot_thread = Thread(target=self.send_screenshots)
        keyboard_thread = Thread(target=self.handle_received_keyboard)
        mouse_thread = Thread(target=self.handle_received_mouse)
        try:
            while True:
                # Wait for request and run thread to do the request
                client_socket, client_address = self.server_socket.accept()
                cmd, data = client_socket.recv(1024).decode('utf-8').split(',')
                if cmd == "Request":
                    self.WriteOnScreen(f"The computer with the ip: {data}, send a request to take over your computer", "action")
                    if self.ask_question_remote(data):
                        self.server_host = data
                        self.server_port = 3450
                        self.run = True
                        client_socket.send("Approved".encode('utf-8'))
                        self.WriteOnScreen(f"You confirmed that computer: {data}, could take over you", "action")
                        self.WriteOnScreen(f"To stop the takeover, click on Stop Remote", "title")
                        screenshot_thread.start()
                        keyboard_thread.start()
                        mouse_thread.start()
                        screenshot_thread.join()
                        keyboard_thread.join()
                        mouse_thread.join()
                        self.stop_remote()
                    else:
                        client_socket.send("Not Approved".encode('utf-8'))
                        self.WriteOnScreen(f"You didn't confirm that computer: {data}, could take over you", "warning")
        except OSError:
            pass

    def validate_entry(self, text, div_dot):
        """
        The function check if the ip(text) is valid and return boolean param.

        Parameters
        ----------
        text : str
            The ip that the user typed
        
        div_dot : int
            how many '.' is a valid ip

        Returns
        -------
        True / False
            If the ip is valid return True else False
        """
        text = str(text)
        parts = text.split(".")
        if not len(parts) == div_dot:
            return False
        else:
            try:
                for i in parts:
                    if int(i) < 0 or int(i) > 256:
                        return False
            except:
                return False
        return True
    
    def start_remote(self):
        """
        The function is called when someone want to take over on someone else and check if the 
        ip is vaild and not connected to someone else.
        If the connection success, it send a request to take over and show some teaching messages.

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        if not self.validate_entry(self.internal_ip.get(), 4):
            self.WriteOnScreen("The external IP is invalid", "warning")
        elif self.run:
            self.WriteOnScreen("The remote desktop still running, please close the window", "warning")
        else:
            self.run = True
            self.server_host = self.internal_ip.get()
            self.WriteOnScreen(f"Connecting to remote computer", "action")
            root.update()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.server_host, self.server_port))
            except:
                self.WriteOnScreen(f"We couldn't communicate with the computer with ip : {self.internal_ip.get()}", "warning")
                self.server_host = None
                self.run = False
            if self.run:
                sock.send(f"Request,{self.user_ip.get()}".encode('utf-8'))
                self.WriteOnScreen(f"A request was sent to the computer with the ip: {self.internal_ip.get()}, to take over the computer", "action")
                data = sock.recv(1024).decode('utf-8')
                if data == "Approved":
                    self.WriteOnScreen(f"The computer approved the takeover request", "action")
                    self.WriteOnScreen(f"To stop the takeover, click on Stop Remote or press esc", "title")
                    self.WriteOnScreen(f"The remote control will start in 10 seconds", "title")
                    time.sleep(10)
                    sock.close()
                    Thread(target=self.start_server_remote).start()
                elif data == "Not Approved":
                    self.WriteOnScreen(f"The computer didn't approve the takeover request", "action")
                    sock.close()
                    self.stop_remote()

    def stop_remote(self):
        """
        The function stop the remote control.

        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        self.run = False
        self.server_port = 7850
        if not self.server_host == None:
            self.server_host = None
            self.WriteOnScreen(f"The connection lost!", "warning")
            Thread(target=self.start_server_request).start()

    def ask_question_remote(self, client_address):
        """
        The function open a window and asking yes/no ques of controling his computer or not and return boolean param.

        Parameters
        ----------
        client_address : str
            The internal ip of the user that want taking over him

        Returns
        -------
        True / False
            If the user accepted the remote control
        """
        res = messagebox.askquestion("Remote Control", f"The computer with the ip : {client_address} want to control your coumpter\n Are you agree?")
        return res == 'yes'
        
    def start_server_remote(self):
        """
        The function work on the controlling computer and start server on user computer and listening for clients.
        The server wait for 3 clients : keyboard, screenshot and mouse and for each of them 
        creating a thread to run this.
        
        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        if not self.server_socket == None:
            self.server_socket.close()
        count_clients = 0
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_host = self.user_ip.get()
        self.server_port = 3450
        try:
            self.server_socket.bind((self.server_host, self.server_port))
            self.server_socket.listen(3)

            while True:
                if self.run:
                    # Wait for request and run thread to do the request
                    client_socket, client_address = self.server_socket.accept()
                    socket_type = client_socket.recv(1024).decode('utf-8')
                    if socket_type == "Keyboard":
                        self.thread_send_keyboard = Thread(target=self.send_keyboard, args=(client_socket,))
                        self.thread_send_keyboard.start()
                        count_clients += 1
                    elif socket_type == "Mouse":
                        self.thread_handle_received_mouse = Thread(target=self.listen_mouse, args=(client_socket,))
                        self.thread_handle_received_mouse.start()
                        count_clients += 1
                    elif socket_type == "Screenshot":
                        self.thread_handle_received_screenshot = Thread(target=self.handle_received_screenshot, args=(client_socket,))
                        self.thread_handle_received_screenshot.start()
                        count_clients += 1
                    if count_clients == 3:
                        self.thread_handle_received_screenshot.join()
                        self.server_socket.close()
                        self.stop_remote()
                        pyautogui.press('esc')
        except WindowsError as e:
            if e.winerror == 10038:
                pass
        except Exception as e:
            self.WriteOnScreen(f"Error starting server: {e}", "warning")
        
    def send_keyboard(self, client_socket):
        """
        The function work on the controlling computer and listening to keyboard events 
        and send them to the other computer.
        
        Parameters
        ----------
        self : self
            The attributes of the class

        client_socket : socket
            The client socket that connect as keyboard

        Returns
        -------
        None
        """
        while self.run:
            try:
                if self.CheckFocusedWindow():
                    button = keyboard.read_event()
                    key_press = button.name
                    if key_press == 'esc':
                        self.run = False
                    else:
                        if button.event_type == keyboard.KEY_DOWN:
                            client_socket.send(int(1).to_bytes(1, byteorder="big"))
                        elif button.event_type == keyboard.KEY_UP:
                            client_socket.send(int(2).to_bytes(1, byteorder="big"))
                        bytes_size = len(key_press.encode('utf-8'))

                        client_socket.send(int(bytes_size).to_bytes(3, byteorder="big"))
                        client_socket.send(key_press.encode('utf-8'))
            except WindowsError:
                return
        client_socket.close()

    def listen_mouse(self, client_socket):
        """
        The function work on the controlling computer and listening to mouse events 
        and send them to the other computer.
        
        Parameters
        ----------
        self : self
            The attributes of the class
        
        client_socket : socket
            The client socket that connect as mouse

        Returns
        -------
        None
        """
        last_x, last_y = pyautogui.position()
        self.otherScreenWidth = int.from_bytes(client_socket.recv(6), byteorder="big")
        self.otherScreenHeight = int.from_bytes(client_socket.recv(6), byteorder="big")

        def check_limit_length(x, y):
            if x >= 0 and y >= 0:
                return True
            return False
        
        def send_mouse_data(action, x=None, y=None, button=None, dx=None, dy=None):
            try:
                if self.CheckFocusedWindow():
                    client_socket.send(int(action).to_bytes(1, byteorder="big"))
                    if x is not None or y is not None:
                        client_socket.send(int((x / self.screenWidth) * self.otherScreenWidth).to_bytes(4, byteorder="big"))
                        client_socket.send(int((y / self.screenHeight) * self.otherScreenHeight).to_bytes(4, byteorder="big"))
                    if button is not None:
                        client_socket.send(int(button).to_bytes(1, byteorder="big"))
                    if dx is not None or dy is not None:
                        client_socket.send(int(dx).to_bytes(4, byteorder="big", signed=True))
                        client_socket.send(int(dy).to_bytes(4, byteorder="big", signed=True))
            except WindowsError as e:
                if e.winerror == 10054:
                    self.run = False
                
        def on_move(x, y):
            nonlocal last_x, last_y
            if check_limit_length(x, y) and (abs(x - last_x) >= 55 or abs(y - last_y) >= 55):
                send_mouse_data(1, x, y)
                last_x, last_y = x, y
                if not self.run:
                    return False
        
        def on_click(x, y, button, pressed):
            if check_limit_length(x, y):
                if pressed:
                    send_mouse_data(1, x, y)
                    send_mouse_data(2, button=4 if button == mouse.Button.left else 5)
                else:
                    send_mouse_data(1, x, y)
                    send_mouse_data(3, button=4 if button == mouse.Button.left else 5)
                if not self.run:
                    return False
            
        def on_scroll(x, y, dx, dy):
            if check_limit_length(x, y):
                send_mouse_data(4, dx=dx, dy=dy)
                if not self.run:
                    return False

        with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
            while self.run:
                listener.join()
        client_socket.close()

    def handle_received_screenshot(self, client_socket):
        """
        The function work on the controlling computer and get data of screenshots that got from the other computer 
        and create a film of pictures.
        The film showed for the controlling computer.
        
        Parameters
        ----------
        self : self
            The attributes of the class
        
        client_socket : socket
            The client socket that connect as mouse

        Returns
        -------
        None
        """
        while self.run:
            try:
                # Receive the length of the screenshot data
                bytes_size = client_socket.recv(4)
                screenshot_size = int.from_bytes(bytes_size, byteorder='big')

                # Receive the screenshot data
                screenshot_data = b''
                remain_size = screenshot_size
                while remain_size > 0:
                    data = client_socket.recv(min(4096, remain_size))
                    screenshot_data += data
                    remain_size -= len(data)

                screenshot = Image.open(io.BytesIO(screenshot_data))
                screenshot = screenshot.resize((self.screenWidth, self.screenHeight))
                img = cv2.cvtColor(numpy.array(screenshot), cv2.COLOR_RGB2BGR)
                cv2.namedWindow("Computer Screen", cv2.WINDOW_NORMAL)
                cv2.setWindowProperty("Computer Screen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                cv2.imshow("Computer Screen", img)
                cv2.waitKey(1)
                if self.window == None:
                    self.window = gw.getWindowsWithTitle("Computer Screen")
            except WindowsError:
                self.run = False
        cv2.destroyAllWindows()
        client_socket.close()
        
    def send_screenshots(self):
        """
        The function work on the controlled computer, connecting to the server of the the controlling computer, 
        take screenshot and send the data of the screenshot to the other computer.
        
        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.server_host, self.server_port))
        sock.send("Screenshot".encode('utf-8'))
        time.sleep(2)
        try:
            while self.run:
                screenshot = ImageGrab.grab(bbox=(0, 0, self.screenWidth, self.screenHeight))
                screenshot_byte_array = io.BytesIO()
                screenshot.save(screenshot_byte_array, format="JPEG")
                screenshot_data = screenshot_byte_array.getvalue()

                sock.send(len(screenshot_data).to_bytes(4, byteorder='big'))
                sock.sendall(screenshot_data)
        except WindowsError:
            self.run = False
        sock.close()

    def handle_received_keyboard(self):
        """
        The function work on the controlled computer, connecting to the server of the the controlling computer, 
        and receive keyboard events and do them on the controlled computer.
        
        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.server_host, self.server_port))
        sock.send("Keyboard".encode('utf-8'))
        while self.run:
            try:
                action = int.from_bytes(sock.recv(1), byteorder="big")
                bytes_size = int.from_bytes(sock.recv(3), byteorder="big")
                button = str(sock.recv(bytes_size).decode('utf-8'))
                if action == 1:
                    keyboard.press(button)
                else:
                    keyboard.release(button)
            except ValueError:
                pass
            except WindowsError:
                self.run = False
        sock.close()

    def handle_received_mouse(self):
        """
        The function work on the controlled computer, connecting to the server of the the controlling computer, 
        and receive mouse events and do them on the controlled computer.
        
        Parameters
        ----------
        self : self
            The attributes of the class

        Returns
        -------
        None
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.server_host, self.server_port))
        sock.send("Mouse".encode('utf-8'))
        sock.send(self.screenWidth.to_bytes(6, byteorder="big"))
        sock.send(self.screenHeight.to_bytes(6, byteorder="big"))
        while self.run:
            try:
                # time.sleep(0.005)
                action_bytes = sock.recv(1)
                action = int.from_bytes(action_bytes, byteorder="big")
                if action == 1: # move
                    x = int.from_bytes(sock.recv(4), byteorder="big")
                    y = int.from_bytes(sock.recv(4), byteorder="big")
                    pyautogui.moveTo(x, y)
                elif action == 2: # click
                    button_size = int.from_bytes(sock.recv(1), byteorder="big")
                    button = "left" if button_size == 4 else "right"
                    pyautogui.mouseDown(button=button)
                elif action == 3: # unclick
                    button_size = int.from_bytes(sock.recv(1), byteorder="big")
                    button = "left" if button_size == 4 else "right"
                    pyautogui.mouseUp(button=button)
                elif action == 4: # scroll
                    dx = int.from_bytes(sock.recv(4), byteorder="big", signed=True)
                    dy = int.from_bytes(sock.recv(4), byteorder="big", signed=True)
                    if dx == 0:
                        pyautogui.scroll(dy * 100)
                    else:
                        pyautogui.hscroll(dx * 100)
            except pyautogui.FailSafeException:
                pyautogui.FAILSAFE = True
                pyautogui.FAILSAFE_POINTS = [(0, 0)]
            except WindowsError:
                self.run = False 
        sock.close()

    def WriteOnScreen(self, result, tag):
        """
        The function show a message in color of tag on tkinter's window.
        
        Parameters
        ----------
        result : str
            The message to show

        tag : str
            The tag responsible for the color of the text

        Returns
        -------
        None
        """
        self.text_status.config(state=tk.NORMAL)
        self.text_status.insert(tk.END, result + "\n\n", tag)
        self.text_status.config(state=tk.DISABLED)
        self.text_status.see(tk.END)
        self.root.update()

    def CheckFocusedWindow(self):
        if not self.window == None:
            if self.window and self.window[0].isActive:
                return True
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteDesktop(root)
    Thread(target=app.start_server_request).start()
    root.mainloop()