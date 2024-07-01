import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from itertools import combinations
import subprocess
import numpy as np

class Counter:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Counter App")
        self.root.geometry("300x150")

        self.points = []
        self.polygons = []
        self.frame = None
        self.resized_width = None
        self.resized_height = None
        self.combination_vars = []
        self.video_path = None

        self.setup_initial_screen()
        self.bind_events()

    def setup_initial_screen(self):
        self.label = tk.Label(self.root)
        self.label.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_label = tk.Label(self.root, text="Please select a video file to start.", wraplength=400, justify='left')
        self.text_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.load_btn = tk.Button(self.root, text="Select Video", command=self.load_video)
        self.load_btn.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    def bind_events(self):
        self.label.bind("<Button-1>", self.get_click)
        self.root.bind("<c>", self.finish_polygon)

    def load_video(self):
        self.video_path = filedialog.askopenfilename()
        if not self.video_path:
            return

        self.cap = cv2.VideoCapture(self.video_path)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        frame_no = int(fps * 5)  # Frame at 5 seconds
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = self.cap.read()
        self.cap.release()

        if not ret:
            messagebox.showerror("Error", "Failed to capture frame at 5 seconds.")
            return

        self.frame = frame
        self.update_layout(frame)
        self.show_frame(frame)

    def update_layout(self, frame):
        x, y = int(frame.shape[1]/1.45), int(frame.shape[0]/2)
        self.root.geometry(f"{x}x{y}")
        self.root.resizable(False, False)

        self.label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.load_btn.pack_forget()

        self.buttons = tk.Frame(self.root)
        self.buttons.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.next_btn = tk.Button(self.buttons, text="Next", command=self.show_polygons)
        self.undo_btn = tk.Button(self.buttons, text="Undo", command=self.undo_last_point)
        self.next_btn.pack(side=tk.RIGHT, fill=tk.X, padx=0, pady=0)
        self.undo_btn.pack(side=tk.LEFT, fill=tk.X, padx=0, pady=0)

        self.text_label.config(text="Click to draw polygons; Press 'c' to complete a polygon; Click 'Next' when done. Click 'Undo' to remove the last point.", wraplength=400, justify='left')

    def show_frame(self, frame):
        self.original_width, self.original_height = frame.shape[1], frame.shape[0]
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        
        desired_height = 500
        aspect_ratio = img.width / img.height
        new_width = int(desired_height * aspect_ratio)
        self.resized_width, self.resized_height = new_width, desired_height
        
        img = img.resize((new_width, desired_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(image=img)
        self.label.config(image=self.photo)
        self.label.image = self.photo

        self.displayed_width, self.displayed_height = new_width, desired_height

    def get_click(self, event):
        if self.frame is None:
            return

        x_offset = (self.label.winfo_width() - self.displayed_width) // 2
        y_offset = (self.label.winfo_height() - self.displayed_height) // 2
        
        x, y = event.x - x_offset, event.y - y_offset
        
        if 0 <= x < self.displayed_width and 0 <= y < self.displayed_height:
            x = int(x * self.original_width / self.displayed_width)
            y = int(y * self.original_height / self.displayed_height)
            
            self.points.append((x, y))
            self.draw_polygons()

    def draw_polygons(self):
        temp_frame = self.frame.copy()
        
        for point in self.points:
            cv2.circle(temp_frame, point, 5, (0, 255, 0), -1)
        
        if len(self.points) > 1:
            cv2.polylines(temp_frame, [np.array(self.points)], False, (0, 255, 0), 2)
        
        for idx, polygon in enumerate(self.polygons):
            cv2.polylines(temp_frame, [np.array(polygon)], True, (0, 255, 0), 2)
            for point in polygon:
                cv2.circle(temp_frame, point, 5, (0, 255, 0), -1)
            cv2.putText(temp_frame, f'Polygon {idx + 1}', polygon[0], cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        self.show_frame(temp_frame)

    def undo_last_point(self):
        if self.points:
            self.points.pop()
            self.draw_polygons()
        else:
            messagebox.showwarning("Warning", "No more points to undo.")

    def finish_polygon(self, event):
        if len(self.points) > 2:
            self.polygons.append(self.points.copy())
            self.points = []
            self.draw_polygons()

    def show_polygons(self):
        self.clear_main_window()
        self.setup_display_frame()
        self.setup_options_frame()
        self.display_polygons()

    def clear_main_window(self):
        for widget in self.root.winfo_children():
            widget.pack_forget()

    def setup_display_frame(self):
        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.video_frame = tk.Frame(self.display_frame)
        self.video_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.poly_label = tk.Label(self.video_frame)
        self.poly_label.pack(expand=True, fill=tk.BOTH)

    def setup_options_frame(self):
        self.options_frame = tk.Frame(self.display_frame, width=300)
        self.options_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.options_frame.pack_propagate(False)

        self.text_label = tk.Label(self.options_frame, text="Please select the combinations of polygons you want to track. Click 'Process Video' when you are ready to start the tracking model.", wraplength=350, justify='left')
        self.text_label.pack(side=tk.TOP, fill=tk.X)

        self.canvas = tk.Canvas(self.options_frame)
        self.scrollbar = ttk.Scrollbar(self.options_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.show_combinations()

        self.process_btn = tk.Button(self.options_frame, text="Process Video", command=self.process_video)
        self.process_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

    def display_polygons(self):
        frame = self.frame.copy()
        for idx, polygon in enumerate(self.polygons):
            cv2.polylines(frame, [np.array(polygon)], True, (0, 255, 0), 2)
            for point in polygon:
                cv2.circle(frame, point, 5, (0, 255, 0), -1)
            cv2.putText(frame, f'Polygon {idx + 1}', polygon[0], cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img = img.resize((self.resized_width, self.resized_height), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.poly_label.imgtk = imgtk
        self.poly_label.configure(image=imgtk)

    def show_combinations(self):
        for combo in combinations(range(1, len(self.polygons) + 1), 2):
            var = tk.IntVar()
            self.combination_vars.append((combo, var))
            
            combo_frame = tk.Frame(self.scrollable_frame)
            combo_frame.pack(fill=tk.X, padx=5, pady=2)
            
            chk = tk.Checkbutton(combo_frame, variable=var, text="")
            chk.pack(side=tk.LEFT)
            
            label = tk.Label(combo_frame, text=f"Combination: {combo}")
            label.pack(side=tk.LEFT)

    def process_video(self):
        original_polygons = [[(int(x * self.frame.shape[1] / self.resized_width),
                               int(y * self.frame.shape[0] / self.resized_height))
                              for x, y in polygon] for polygon in self.polygons]
        selected_combinations = [combo for combo, var in self.combination_vars if var.get() == 1]
        
        with open("polygons_combinations.txt", "w") as f:
            f.write(f"{original_polygons}\n")
            f.write(f"{selected_combinations}\n")
            f.write(f"{self.video_path}\n")
        
        try:
            result = subprocess.run(["python", "process_video.py"], capture_output=True, text=True, check=True)
            messagebox.showinfo("Success", "Processing has been finished. Please check car_tracking_results.csv file.")
        except subprocess.CalledProcessError as e:
            error_message = f"An error has occurred! Please try again.\n\nError details: {e.stderr}"
            messagebox.showerror("Error", error_message)

if __name__ == "__main__":
    root = tk.Tk()
    player = Counter(root)
    root.mainloop()