import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
import base64
from PIL import Image, ImageTk
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- CRYPTOGRAPHY ENGINE ---
class CryptoEngine:
    @staticmethod
    def get_key(password: str) -> bytes:
        salt = b"secure_salt_123"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @classmethod
    def encrypt(cls, msg: str, pwd: str) -> str:
        f = Fernet(cls.get_key(pwd))
        return f.encrypt(msg.encode()).decode()

    @classmethod
    def decrypt(cls, token: str, pwd: str) -> str:
        try:
            f = Fernet(cls.get_key(pwd))
            return f.decrypt(token.encode()).decode()
        except:
            return "DECRYPTION_FAILED: Wrong Password or No Message"

# --- MAIN GUI APPLICATION ---
class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSC DFIS - Secure Stego Tool")
        self.root.geometry("1000x900")
        self.root.configure(bg="#0a0a0a")
        
        self.current_img = None
        self.encoded_img = None
        self.video_path = None

        self.main_frame = tk.Frame(self.root, bg="#0a0a0a")
        self.main_frame.pack(fill="both", expand=True)
        
        self._build_ui()

        self.cap = None
        self.playing = False


    def _build_ui(self):
        # 1. MOVING MARQUEE
        self.marquee_text = " >>> SECURE VIDEO AND IMAGE STEGANOGRAPHY SYSTEM - AES 256 BIT ENCRYPTION ENABLED - BE SECURED ALWAYS<<< "
        self.marquee_label = tk.Label(self.main_frame, text=self.marquee_text, fg="cyan", bg="#1a1a1a", font=("Courier", 16, "bold"))
        self.marquee_label.pack(fill="x")
        self._animate_marquee()
        

        # 2. HEADER
        tk.Label(self.main_frame, text="SECURE IMAGE AND VIDEO STEGO TOOL", fg="#00ff00", bg="#0a0a0a", font=("Fixedsys", 20, "bold")).pack(pady=10)

        # 3. NEW ZOOM CONTROLS
        zoom_frame = tk.Frame(self.main_frame, bg="#0a0a0a")
        zoom_frame.pack(pady=5)
        
        tk.Button(zoom_frame, text=" Zoom In (+) ", command=lambda: self.adjust_zoom(0.2), 
                  bg="#333", fg="pink", font=("Arial", 8, "bold")).grid(row=0, column=0, padx=5)
        tk.Button(zoom_frame, text=" Zoom Out (-) ", command=lambda: self.adjust_zoom(-0.2), 
                  bg="#333", fg="pink", font=("Arial", 8, "bold")).grid(row=0, column=1, padx=5)
        tk.Button(zoom_frame, text=" Reset Zoom ", command=self.reset_zoom, 
                  bg="#333", fg="pink", font=("Arial", 8, "bold")).grid(row=0, column=2, padx=5)
     # 4. PREVIEW CANVAS
        self.canvas_frame = tk.Frame(self.main_frame, bg="#111", width=600, height=350, highlightbackground="#00ff00", highlightthickness=1)
        self.canvas_frame.pack(pady=10)
        self.img_label = tk.Label(self.canvas_frame, bg="#111")
        self.img_label.pack()

        # 5. INPUT FIELDS
        input_frame = tk.Frame(self.main_frame, bg="#0a0a0a")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Type Secret Message:", fg="yellow", bg="#0a0a0a", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.txt_input = tk.Text(input_frame, height=4, width=60, bg="#1a1a1a", fg="#00ff00", insertbackground="white", font=("Consolas", 11))
        self.txt_input.grid(row=1, column=0, pady=5)

        tk.Label(input_frame, text="Type Encryption Password (key):", fg="yellow", bg="#0a0a0a", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(10,0))
        self.pwd_input = tk.Entry(input_frame, show="*", width=60, bg="#1a1a1a", fg="#ffff00", font=("Consolas", 12))
        self.pwd_input.grid(row=3, column=0, pady=5)

        # 6. BUTTON GRID
        btn_frame = tk.Frame(self.main_frame, bg="#0a0a0a")
        btn_frame.pack(pady=20)

        def create_btn(parent, text, cmd, row, col, color="#222"):
            btn = tk.Button(parent, text=text, command=cmd, width=18, height=2,
                            bg=color, fg="white", font=("Arial", 9, "bold"),
                            activebackground="#00ff00", relief="solid", cursor="hand2") # relief="flat",
            btn.grid(row=row, column=col, padx=8, pady=8)
            return btn

        create_btn(btn_frame, "Load Image", self.load_image, 0, 0 ,color="magenta" )
        create_btn(btn_frame, "Encode Image", self.encode_image, 0, 1, color="magenta")
        create_btn(btn_frame, "Decode Image", self.decode_image, 0, 2, color="magenta")
        create_btn(btn_frame, "Save Image", self.save_image, 0, 3, color="magenta") #color="#005500"
        create_btn(btn_frame, "Detect Image Steg", self.detect_image_steg, 0, 4, color="blue")

        create_btn(btn_frame, "Load Video", self.load_video, 1, 0, color="red")
        create_btn(btn_frame, "Encode Video", self.encode_video, 1, 1, color="red")
        create_btn(btn_frame, "Decode Video", self.decode_video, 1, 2, color="red")
        create_btn(btn_frame, "Detect Video Steg", self.detect_video_steg, 1, 3, color="blue")

        create_btn(btn_frame, "Refresh", self.reset, 2, 1, color="#005500")
        create_btn(btn_frame, "Exit", self.on_exit, 2, 2, color="#005500")

        progress_container = tk.Frame(self.main_frame, bg="#0a0a0a")
        progress_container.pack(side="bottom", fill="x")

        # BOTTOM CONTAINER (HOLDS BOTH PROGRESS + FOOTER)
        #bottom_frame = tk.Frame(self.root, bg="#0a0a0a")
        #bottom_frame.pack(side="bottom", fill="x")

        # PROGRESS BAR
        #self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        #self.progress.pack(fill="x", padx=10, pady=5)

        # FOOTER TEXT
        #footer_text = "© 2026 Mawanda Ivan | SECURE STEG TOOL (Image & Video) | All Rights Reserved"
        #tk.Label(bottom_frame, text=footer_text, fg="#555", bg="#0a0a0a", font=("Arial", 14)).pack(pady=5)
        # FIXED BOTTOM BAR
        bottom_bar = tk.Frame(self.root, bg="#0a0a0a")
        bottom_bar.pack(side="bottom", fill="x")

        # PROGRESS BAR
        self.progress = ttk.Progressbar(bottom_bar, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        # FOOTER TEXT
        footer_text = "© 2026 Mawanda Ivan | SECURE STEG TOOL (Image & Video) | All Rights Reserved"
        tk.Label(bottom_bar, text=footer_text, fg="#555", bg="#0a0a0a",font=("Arial", 14)).pack(pady=5)
        
    # --- NEW ZOOM METHODS ---
    def adjust_zoom(self, delta):
        """Update zoom level and refresh preview."""
        if self.current_img is not None:
            self.zoom_level = max(0.1, min(self.zoom_level + delta, 5.0))
            img_to_show = self.encoded_img if self.encoded_img is not None else self.current_img
            self._update_preview(img_to_show)

    def reset_zoom(self):
        """Restore zoom to original scale."""
        if self.current_img is not None:
            self.zoom_level = 1.0
            img_to_show = self.encoded_img if self.encoded_img is not None else self.current_img
            self._update_preview(img_to_show)

    # --- MODIFIED LOGIC METHODS ---
    def _animate_marquee(self):
        self.marquee_text = self.marquee_text[1:] + self.marquee_text[0]
        self.marquee_label.config(text=self.marquee_text)
        self.root.after(150, self._animate_marquee)

    def _update_preview(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        
        # Calculate new dimensions based on zoom_level
        base_w, base_h = 550, 330
        zoom_w = int(base_w * self.zoom_level)
        zoom_h = int(base_h * self.zoom_level)
        
        im.thumbnail((zoom_w, zoom_h))
        imgtk = ImageTk.PhotoImage(image=im)
        self.img_label.config(image=imgtk)
        self.img_label.image = imgtk

    def load_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.current_img = cv2.imread(path)
            self.zoom_level = 1.0 
            self._update_preview(self.current_img)

    def encode_image(self):
        if self.current_img is None: return
        msg = self.txt_input.get("1.0", "end-1c")
        pwd = self.pwd_input.get()
        if not msg or not pwd:
            messagebox.showwarning("Input Error", "Message and Password required!")
            return
        
        encrypted = CryptoEngine.encrypt(msg, pwd) + "@@END@@"
        binary_msg = ''.join(format(ord(c), '08b') for c in encrypted)
        
        flat = self.current_img.flatten()
        bits = np.array([int(b) for b in binary_msg], dtype=np.uint8)
        
        if len(bits) > len(flat):
            messagebox.showerror("Limit Exceeded", "Message too long for this image.")
            return

        flat[:len(bits)] = (flat[:len(bits)] & 254) | bits
        self.encoded_img = flat.reshape(self.current_img.shape)
        self._update_preview(self.encoded_img)
        messagebox.showinfo("Success", "Message encoded in memory Waiting to be saved.")

    def save_image(self):
        if self.encoded_img is None:
            messagebox.showerror("Error", "No encoded image to save!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            cv2.imwrite(path, self.encoded_img)
            messagebox.showinfo("Saved", "Image saved successfully.")

    def detect_image_steg(self):
        if self.current_img is None:
            messagebox.showerror("Error", "Load an image first!")
            return

        flat = self.current_img.flatten()
        lsb = np.mod(flat, 2)

    # Convert to bytes
        byte_data = np.packbits(lsb[:(len(lsb)//8)*8]).tobytes()
        decoded = byte_data.decode('ascii', errors='ignore')

    # Detection logic
        if "@@END@@" in decoded:
            messagebox.showinfo("Detection Result", "⚠️ Steganography DETECTED (Hidden message marker found)")
            return

    # Statistical randomness check
        ones = np.sum(lsb)
        zeros = len(lsb) - ones
        ratio = ones / len(lsb)

        if 0.45 < ratio < 0.55:
            messagebox.showwarning("Detection Result", "⚠️ POSSIBLE steganography detected (LSB randomness suspicious)")
        else:
            messagebox.showinfo("Detection Result", "✅ No steganography detected")

    def load_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
        if self.video_path:
            messagebox.showinfo("Video Ready", "Video file loaded.")
            self.cap = cv2.VideoCapture(self.video_path)
            self.playing = True
            self.play_video()

    def play_video(self):
        if self.cap is None or not self.playing:
            return

        ret, frame = self.cap.read()

        if ret:
            self.current_img = frame
            if not hasattr(self, 'zoom_level'):
                self.zoom_level = 1.0
            self._update_preview(frame)

        # control playback speed (30ms ≈ ~30fps)
            self.root.after(30, self.play_video)
        else:
        # restart video automatically
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.root.after(30, self.play_video)

    def detect_video_steg(self):
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
        if not path:
            return

        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()

        if not ret:
            messagebox.showerror("Error", "Failed to read video.")
            cap.release()
            return

        flat = frame.flatten()
        lsb = np.mod(flat, 2)

        byte_data = np.packbits(lsb[:(len(lsb)//8)*8]).tobytes()
        decoded = byte_data.decode('ascii', errors='ignore')

        if "@@END@@" in decoded:
            messagebox.showinfo("Detection Result", "⚠️ Steganography DETECTED in video (frame 1)")
            cap.release()
            return

        ones = np.sum(lsb)
        ratio = ones / len(lsb)

        if 0.45 < ratio < 0.55:
            messagebox.showwarning("Detection Result", "⚠️ POSSIBLE video steganography detected")
        else:
            messagebox.showinfo("Detection Result", "✅ No steganography detected in video")

        cap.release()

    
    def encode_video(self):
        if not self.video_path: return
        out_path = filedialog.asksaveasfilename(defaultextension=".mkv")
        if not out_path: return

        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        fourcc = cv2.VideoWriter_fourcc(*'FFV1') # Lossless
        fps, w, h = cap.get(cv2.CAP_PROP_FPS), int(cap.get(3)), int(cap.get(4))
        writer = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
        frame_count = 0
        
        ret, frame = cap.read()
        if ret:
            # Re-use image encoding logic for the first frame
            msg = self.txt_input.get("1.0", "end-1c")
            pwd = self.pwd_input.get()
            encrypted = CryptoEngine.encrypt(msg, pwd) + "@@END@@"
            binary_msg = ''.join(format(ord(c), '08b') for c in encrypted)
            
            flat = frame.flatten()
            bits = np.array([int(b) for b in binary_msg], dtype=np.uint8)
            flat[:len(bits)] = (flat[:len(bits)] & 254) | bits
            writer.write(flat.reshape(frame.shape))

            frame_count +=1
            
            while True:
                ret, frame = cap.read()
                if not ret: break
                writer.write(frame)
                frame_count +=1
                #UPDATE PROGRESS BAR
                progress_percent = (frame_count / total_frames) *100
                self.progress['value'] = progress_percent
                self.root.update_idletasks()
        
        cap.release()
        writer.release()
        self.progress['value'] = 0 #reset after completion
        messagebox.showinfo("Video Saved Automatically for maximum Integrity", f"Encoded video saved to:\n{out_path}")

    def decode_image(self):
        if self.current_img is None: return
        flat = self.current_img.flatten()
        bits = np.mod(flat, 2)
        byte_chunks = np.packbits(bits[:(len(bits)//8)*8]).tobytes()
        
        decoded_str = ""
        for char in byte_chunks.decode('ascii', errors='ignore'):
            decoded_str += char
            if decoded_str.endswith("@@END@@"):
                clean = decoded_str.replace("@@END@@", "")
                res = CryptoEngine.decrypt(clean, self.pwd_input.get())
                self.txt_input.delete("1.0", tk.END)
                self.txt_input.insert(tk.END, res)
                return
        messagebox.showwarning("Failed", "No hidden message found.")

    def decode_video(self):
        path = filedialog.askopenfilename()
        if not path: return
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        if ret:
            self.current_img = frame
            self.decode_image()
        cap.release()

    #def save_video_info(self):
        #messagebox.showinfo("Note", "Video is automatically saved to your chosen path during the 'ENCODE VIDEO' process to ensure data integrity.")

    def reset(self):
        self.current_img = None
        self.encoded_img = None
        self.video_path = None

        self.playing = False
        if self.cap:
            self.cap.release()
            self.cap = None

        self.img_label.config(image="")
        self.txt_input.delete("1.0", tk.END)
        self.pwd_input.delete(0, tk.END)
        messagebox.showinfo("Reset", "System cleared.")
        
    def on_exit(self):
        self.root.destroy()

    # ---------- LOGIN SYSTEM ----------

class LoginPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Login - Secure Stego Tool")
        self.root.geometry("400x300")
        self.root.configure(bg="black")

        tk.Label(root, text="LOGIN", font=("Courier", 20, "bold"),
                 fg="lime", bg="black").pack(pady=20)

        tk.Label(root, text="Username", fg="white", bg="black").pack()
        self.username = tk.Entry(root)
        self.username.pack(pady=5)

        tk.Label(root, text="Password", fg="white", bg="black").pack()
        self.password = tk.Entry(root, show="*")
        self.password.pack(pady=5)

        tk.Button(root, text="LOGIN", command=self.check_login,
                  bg="green", fg="white", width=15).pack(pady=20)

    def check_login(self):
        user = self.username.get()
        pwd = self.password.get()

        # 🔐 Simple credentials (you can change)
        if user == "admin" and pwd == "admin":
            messagebox.showinfo("Success", "Login Successful!")

            # Destroy login window
            self.root.destroy()

            # Open main app
            main_root = tk.Tk()
            app = StegoApp(main_root)
            main_root.mainloop()

        else:
            messagebox.showerror("Error", "Invalid Username or Password")

# ---------- MAIN ----------

if __name__ == "__main__":
    root = tk.Tk()
    login = LoginPage(root)
    root.mainloop()

