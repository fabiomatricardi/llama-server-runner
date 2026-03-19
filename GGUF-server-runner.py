import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import re
import psutil 
import webbrowser

class GgufServerRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("GGUF Server Runner v1.6")
        self.root.geometry("950x620") 
        self.process = None
        self.is_stopping = False

        # --- Check for Binaries ---
        self.check_binaries()

        # System hardware detection
        mem = psutil.virtual_memory()
        self.total_sys_ram_gb = mem.total / (1024**3)
        self.max_threads = psutil.cpu_count(logical=True)

        # --- 1. Model Selection ---
        tk.Label(root, text="Model File (GGUF):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.model_path = tk.StringVar()
        tk.Entry(root, textvariable=self.model_path, width=75).grid(row=0, column=1, padx=5)
        tk.Button(root, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5)

        # --- 2. Multimodal Projector (mmproj) ---
        tk.Label(root, text="Multimodal Projector:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.mmproj_path = tk.StringVar()
        tk.Entry(root, textvariable=self.mmproj_path, width=75).grid(row=1, column=1, padx=5)
        tk.Button(root, text="Browse", command=self.browse_mmproj).grid(row=1, column=2, padx=5)

        # --- 3. Server Networking & Settings ---
        net_frame = tk.LabelFrame(root, text=" Server Settings ")
        net_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

        tk.Label(net_frame, text="Port:").pack(side="left", padx=5)
        self.port = tk.IntVar(value=8080)
        tk.Entry(net_frame, textvariable=self.port, width=8).pack(side="left", padx=5)

        self.share_net = tk.BooleanVar(value=False)
        tk.Checkbutton(net_frame, text="Share on Local Network (0.0.0.0)", variable=self.share_net).pack(side="left", padx=20)

        self.auto_browser = tk.BooleanVar(value=True)
        tk.Checkbutton(net_frame, text="Auto-Launch Browser", variable=self.auto_browser).pack(side="left", padx=5)

        # --- 4. Parameters ---
        param_frame = tk.Frame(root)
        param_frame.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        tk.Label(param_frame, text="GPU Layers:").pack(side="left")
        self.ngl = tk.IntVar(value=0)
        tk.Spinbox(param_frame, from_=0, to=999, textvariable=self.ngl, width=5).pack(side="left", padx=5)

        tk.Label(param_frame, text="Threads:").pack(side="left", padx=5)
        self.threads = tk.IntVar(value=min(1, self.max_threads))
        tk.Spinbox(param_frame, from_=1, to=self.max_threads, textvariable=self.threads, width=5).pack(side="left", padx=5)

        tk.Label(param_frame, text="Context:").pack(side="left", padx=5)
        self.context = tk.IntVar(value=4096)
        tk.Spinbox(param_frame, from_=512, to=128000, textvariable=self.context, width=8).pack(side="left", padx=5)

        tk.Label(param_frame, text="Batch Size:").pack(side="left", padx=5)
        self.batch_size = tk.StringVar(value="2048")
        tk.Spinbox(param_frame, values=["512", "1024", "2048", "4096", "8192"], textvariable=self.batch_size, width=7).pack(side="left", padx=5)

        tk.Label(param_frame, text="Reasoning Budget (-1 unlimited, 0 no reasoning:").pack(side="left", padx=5)
        self.reasoning_budget = tk.IntVar(value=0)
        tk.Spinbox(param_frame, from_=-1, to=8192, textvariable=self.reasoning_budget, width=6).pack(side="left", padx=5)

        cb_frame = tk.Frame(root)
        cb_frame.grid(row=4, column=0, columnspan=3, sticky="w", padx=10)
        self.ctk_var, self.ctv_var, self.fa_var, self.embed_var = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        tk.Checkbutton(cb_frame, text="Quantize K Cache", variable=self.ctk_var).pack(side="left", padx=5)
        tk.Checkbutton(cb_frame, text="Quantize V Cache", variable=self.ctv_var).pack(side="left", padx=5)
        tk.Checkbutton(cb_frame, text="Flash Attention", variable=self.fa_var).pack(side="left", padx=5)
        tk.Checkbutton(cb_frame, text="Enable Embeddings", variable=self.embed_var).pack(side="left", padx=20)

        # --- 5. Info & Performance Panel ---
        info_frame = tk.LabelFrame(root, text=" Live Model Stats & Performance ", fg="blue", font=("Arial", 10, "bold"))
        info_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        
        self.stat_layers = tk.StringVar(value="Layers: -")
        self.stat_free_ram = tk.StringVar(value=f"System Available: {mem.available/(1024**3):.2f} GB")
        self.stat_model_ram = tk.StringVar(value="Weights: -")
        self.stat_kv_ram = tk.StringVar(value="KV Cache: -")
        self.stat_buffer_ram = tk.StringVar(value="Compute Buffer: -")
        self.stat_total_ram = tk.StringVar(value="Model Est. Total: -")
        self.stat_prompt_speed = tk.StringVar(value="Prompt: -")
        self.stat_gen_speed = tk.StringVar(value="Gen: -")

        tk.Label(info_frame, textvariable=self.stat_layers).grid(row=0, column=0, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_free_ram, fg="green").grid(row=0, column=1, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_model_ram).grid(row=1, column=0, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_kv_ram).grid(row=1, column=1, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_buffer_ram).grid(row=2, column=0, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_total_ram, font=("Arial", 9, "bold")).grid(row=2, column=1, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_prompt_speed, fg="purple", font=("Arial", 9, "bold")).grid(row=3, column=0, padx=20, sticky="w")
        tk.Label(info_frame, textvariable=self.stat_gen_speed, fg="darkred", font=("Arial", 9, "bold")).grid(row=3, column=1, padx=20, sticky="w")

        self.canvas_width = 840
        self.canvas = tk.Canvas(info_frame, width=self.canvas_width, height=25, bg="#e0e0e0", highlightthickness=1)
        self.canvas.grid(row=4, column=0, columnspan=2, padx=20, pady=5)

        # --- 6. Controls ---
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=5)
        self.server_btn = tk.Button(btn_frame, text="Run Server", command=lambda: self.start_task("server"), bg="#28a745", fg="white", width=12)
        self.server_btn.pack(side="left", padx=5)
        self.inspect_btn = tk.Button(btn_frame, text="Inspect/Benchmark", command=lambda: self.start_task("inspect"), bg="#007bff", fg="white", width=18)
        self.inspect_btn.pack(side="left", padx=5)
        tk.Button(btn_frame, text="Stop", command=self.stop_process, bg="#dc3545", fg="white", width=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Copy Command", command=self.copy_command, width=14).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear Log", command=self.clear_all, width=10).pack(side="left", padx=5)

        self.status_label = tk.Label(root, text="System: Idle | PID: None", fg="grey")
        self.status_label.grid(row=7, column=0, columnspan=3)

        self.output_text = tk.Text(root, height=12, width=120, font=("Consolas", 9))
        self.output_text.grid(row=8, column=0, columnspan=3, padx=10, pady=5)

        self.current_model_mib = self.current_kv_mib = self.current_compute_mib = 0.0
        self.current_mode = "server"
        self.draw_ram_bar(0)

    def check_binaries(self):
        missing = [f for f in ["llama-cli.exe", "llama-server.exe"] if not os.path.exists(f)]
        if missing:
            temp_root = tk.Tk(); temp_root.withdraw()
            messagebox.showerror("Missing Files", f"Required binaries missing in current directory: {', '.join(missing)}")
            temp_root.destroy(); exit()

    def browse_file(self):
        fn = filedialog.askopenfilename(filetypes=[("GGUF files", "*.gguf")])
        if fn: self.model_path.set(fn)

    def browse_mmproj(self):
        fn = filedialog.askopenfilename(filetypes=[("GGUF mmproj files", "*.gguf")])
        if fn: self.mmproj_path.set(fn)

    def copy_command(self):
        cmd = self.build_command("server")
        self.root.clipboard_clear(); self.root.clipboard_append(" ".join(cmd))
        messagebox.showinfo("Clipboard", "Server command copied to clipboard!")

    def parse_line(self, line):
        if "Host" in line and "=" in line and "+" in line:
            m = re.search(r"\|\s+-\s+Host\s+\|\s+\d+\s+=\s+([\d\.]+)\s+\+\s+([\d\.]+)\s+\+\s+([\d\.]+)", line)
            if m:
                self.current_model_mib, self.current_kv_mib, self.current_compute_mib = map(float, m.groups())
                self.stat_model_ram.set(f"Weights: {self.current_model_mib:.2f} MiB")
                self.stat_kv_ram.set(f"KV Cache: {self.current_kv_mib:.2f} MiB")
                self.stat_buffer_ram.set(f"Compute Buffer: {self.current_compute_mib:.2f} MiB")

        if self.current_mode == "inspect" and "does not logits computation" in line:
            self.stat_gen_speed.set("Gen: Embedding model confirmed"); return 

        if self.current_mode == "inspect" and "Prompt:" in line and "Generation:" in line:
            if "Embedding" not in self.stat_gen_speed.get():
                m = re.search(r"Prompt:\s+([\d\.]+)\s+t/s\s+\|\s+Generation:\s+([\d\.]+)\s+t/s", line)
                if m:
                    self.stat_prompt_speed.set(f"Prompt: {m.group(1)} t/s")
                    self.stat_gen_speed.set(f"Gen: {m.group(2)} t/s")

        if self.current_mode == "server" and self.auto_browser.get() and "server is listening on" in line.lower():
            threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{self.port.get()}")).start()
        self.update_total_ram_display()

    def update_total_ram_display(self):
        total_gb = (self.current_model_mib + self.current_kv_mib + self.current_compute_mib) / 1024
        self.stat_total_ram.set(f"Model Est. Total: {total_gb:.2f} GB")
        self.draw_ram_bar(total_gb)

    def draw_ram_bar(self, est_model_gb):
        self.canvas.delete("all")
        mem = psutil.virtual_memory()
        used_now_gb = (mem.total - mem.available) / (1024**3)
        px_used = (used_now_gb / self.total_sys_ram_gb) * self.canvas_width
        px_model = (est_model_gb / self.total_sys_ram_gb) * self.canvas_width
        self.canvas.create_rectangle(0, 0, self.canvas_width, 25, fill="#00FF00", outline="")
        self.canvas.create_rectangle(0, 0, px_used, 25, fill="#999999", outline="")
        color = "#cc0000" if (used_now_gb + est_model_gb) > self.total_sys_ram_gb else "#3366cc"
        self.canvas.create_rectangle(px_used, 0, min(self.canvas_width, px_used + px_model), 25, fill=color, outline="")

    def execute_command(self, cmd):
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True, creationflags=0x08000000, errors="replace")
            self.status_label.config(text=f"Status: Running ({self.current_mode}) | PID: {self.process.pid}")
            while not self.is_stopping:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None: break
                if line:
                    self.output_text.insert(tk.END, line); self.output_text.see(tk.END); self.parse_line(line); self.root.update_idletasks() 
            if self.process: self.process.terminate()
            self.status_label.config(text="Status: Idle | PID: None")
            self.is_stopping = False
            self.server_btn.config(state="normal"); self.inspect_btn.config(state="normal")
        except Exception as e: 
            messagebox.showerror("Error", str(e)); self.server_btn.config(state="normal")

    def stop_process(self):
        if self.process: self.is_stopping = True; self.process.terminate()

    def clear_all(self):
        self.output_text.delete(1.0, tk.END)
        self.stat_prompt_speed.set("Prompt: -"); self.stat_gen_speed.set("Gen: -")

    def build_command(self, mode):
        # Mandatory --mmap enabled for both executables
        if mode == "inspect":
            cmd = [".\\llama-cli.exe", "-m", self.model_path.get(), "--mmap", "-ngl", str(self.ngl.get()), "-t", str(self.threads.get()), "-c", str(self.context.get()), "-st", "-lv", "3", "-n", "100", "-p", "Explain CPU vs GPU inference."]
        else:
            host = "0.0.0.0" if self.share_net.get() else "127.0.0.1"
            cmd = [".\\llama-server.exe", "-m", self.model_path.get(), "--mmap", "-ngl", str(self.ngl.get()), "-t", str(self.threads.get()), "-c", str(self.context.get()), "--host", host, "--port", str(self.port.get()), "-b", self.batch_size.get()]
            if self.embed_var.get(): cmd.append("--embedding")
        
        cmd.extend(["--reasoning-budget", str(self.reasoning_budget.get())])
        if self.mmproj_path.get(): cmd.extend(["--mmproj", self.mmproj_path.get()])
        if self.ctk_var.get(): cmd.extend(['-ctk', 'q8_0'])
        if self.ctv_var.get(): cmd.extend(['-ctv', 'q8_0'])
        if self.fa_var.get(): cmd.extend(['-fa', 'on'])
        return cmd

    def start_task(self, mode):
        if self.process and self.process.poll() is None: return messagebox.showwarning("Busy", "Process already running.")
        if not self.model_path.get(): return messagebox.showerror("Error", "Select model.")
        self.current_mode = mode; cmd = self.build_command(mode)
        self.output_text.delete(1.0, tk.END)
        self.server_btn.config(state="disabled"); self.inspect_btn.config(state="disabled")
        threading.Thread(target=self.execute_command, args=(cmd,), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk(); app = GgufServerRunner(root); root.mainloop()