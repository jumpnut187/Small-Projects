import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import time
import psutil
import queue
import os
import signal
import shutil
from datetime import datetime
import webbrowser
import platform

# Determine system type
PLATFORM = platform.system()
IS_MACOS = PLATFORM == "Darwin"

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

class OpenWebUIController:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenWebUI Controller")
        self.root.geometry("800x600")
        
        # Process variables
        self.process = None
        self.running = False
        self.output_queue = queue.Queue()
        
        # Command configuration
        self.command_var = tk.StringVar(value="open-webui")
        
        # Ollama variables
        self.ollama_process = None
        self.ollama_running = False
        
        # Create the GUI
        self.create_widgets()
        
        # Update resources periodically
        self.check_and_update_command_status()
        
        # Start monitoring system resources
        self.update_resources()
        
        # Start checking the output queue
        self.check_queue()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        # Command entry
        ttk.Label(config_frame, text="Command:").grid(row=0, column=0, sticky=tk.W, padx=5)
        cmd_entry = ttk.Entry(config_frame, textvariable=self.command_var, width=30)
        cmd_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Browse button for command
        browse_btn = ttk.Button(config_frame, text="Browse", command=self.browse_command)
        browse_btn.grid(row=0, column=2, padx=5)
        
        # Installation status and help
        self.cmd_status_var = tk.StringVar(value="Checking command...")
        self.cmd_status_label = ttk.Label(config_frame, textvariable=self.cmd_status_var, foreground="orange")
        self.cmd_status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # Installation help frame
        self.install_frame = ttk.Frame(config_frame)
        self.install_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Install button
        self.install_btn = ttk.Button(self.install_frame, text="Install OpenWebUI", command=self.install_open_webui)
        self.install_btn.pack(side=tk.LEFT, padx=5)
        
        # Documentation link
        self.docs_link = ttk.Label(self.install_frame, text="Documentation", foreground="blue", cursor="hand2")
        self.docs_link.pack(side=tk.LEFT, padx=10)
        self.docs_link.bind("<Button-1>", lambda e: webbrowser.open("https://docs.openwebui.com/"))
        
        # Installation instructions
        self.install_instructions = ttk.Label(config_frame, 
            text="You can install OpenWebUI with: pip install open-webui", 
            wraplength=500)
        self.install_instructions.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        # Start button
        self.start_btn = ttk.Button(control_frame, text="Start OpenWebUI", command=self.start_service)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_btn = ttk.Button(control_frame, text="Stop OpenWebUI", command=self.stop_service, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Status: Not Running")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=20)
        
        # Add clickable link to localhost
        self.localhost_link = ttk.Label(control_frame, text="http://localhost:8080", 
                                        foreground="blue", cursor="hand2")
        self.localhost_link.pack(side=tk.LEFT, padx=5)
        self.localhost_link.bind("<Button-1>", lambda e: webbrowser.open("http://localhost:8080"))
        
        # Resources frame
        resources_frame = ttk.LabelFrame(main_frame, text="System Resources", padding="10")
        resources_frame.pack(fill=tk.X, pady=5)
        
        # CPU usage
        ttk.Label(resources_frame, text="CPU Usage:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cpu_var = tk.StringVar(value="0%")
        ttk.Label(resources_frame, textvariable=self.cpu_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.cpu_progress = ttk.Progressbar(resources_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.cpu_progress.grid(row=0, column=2, padx=5)
        
        # Memory usage
        ttk.Label(resources_frame, text="Memory Usage:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.memory_var = tk.StringVar(value="0%")
        ttk.Label(resources_frame, textvariable=self.memory_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        self.memory_progress = ttk.Progressbar(resources_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.memory_progress.grid(row=1, column=2, padx=5)
        
        # GPU usage (if available)
        ttk.Label(resources_frame, text="GPU Usage:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.gpu_var = tk.StringVar(value="Not available")
        ttk.Label(resources_frame, textvariable=self.gpu_var).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        self.gpu_progress = ttk.Progressbar(resources_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.gpu_progress.grid(row=2, column=2, padx=5)
        
        # GPU memory (if available)
        ttk.Label(resources_frame, text="GPU Memory:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.gpu_memory_var = tk.StringVar(value="Not available")
        ttk.Label(resources_frame, textvariable=self.gpu_memory_var).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        self.gpu_memory_progress = ttk.Progressbar(resources_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.gpu_memory_progress.grid(row=3, column=2, padx=5)
        
        # Process info if running
        ttk.Label(resources_frame, text="Process Memory:").grid(row=4, column=0, sticky=tk.W, padx=5)
        self.proc_mem_var = tk.StringVar(value="N/A")
        ttk.Label(resources_frame, textvariable=self.proc_mem_var).grid(row=4, column=1, sticky=tk.W, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Terminal Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Add timestamp to log
        self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Application started")

    def check_and_update_command_status(self):
        """Check if the specified command exists and update the UI accordingly"""
        command = self.command_var.get().strip()
        is_executable = os.path.isfile(command) and os.access(command, os.X_OK)
        
        if is_executable or self.check_command_exists(command):
            self.cmd_status_var.set("✓ Command found")
            self.cmd_status_label.config(foreground="green")
            self.install_frame.pack_forget()
            self.install_instructions.grid_forget()
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.cmd_status_var.set("✗ Command not found")
            self.cmd_status_label.config(foreground="red")
            self.install_frame.pack(side=tk.LEFT)
            self.install_instructions.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
            self.start_btn.config(state=tk.DISABLED)
        
        # Schedule to check again when command changes
        self.command_var.trace_add("write", lambda *args: self.root.after(500, self.check_and_update_command_status))

    def install_open_webui(self):
        """Install OpenWebUI using pip"""
        self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installing OpenWebUI...")
        
        def run_installation():
            try:
                process = subprocess.Popen(
                    "pip install open-webui",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=True
                )
                
                # Read output
                for line in iter(process.stdout.readline, ''):
                    if line:
                        self.output_queue.put(line.strip())
                
                # Wait for process to complete
                process.wait()
                
                if process.returncode == 0:
                    self.output_queue.put(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OpenWebUI installed successfully")
                    self.root.after(0, self.check_and_update_command_status)
                else:
                    self.output_queue.put(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installation failed with return code {process.returncode}")
            except Exception as e:
                self.output_queue.put(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Installation error: {str(e)}")
        
        # Run installation in a separate thread
        threading.Thread(target=run_installation, daemon=True).start()

    def browse_command(self):
        """Open a file browser to select the command executable"""
        filename = filedialog.askopenfilename(
            title="Select OpenWebUI executable",
            filetypes=[("All files", "*.*")]
        )
        if filename:
            self.command_var.set(filename)
            self.check_and_update_command_status()

    def check_command_exists(self, command):
        """Check if the specified command exists in PATH"""
        return shutil.which(command) is not None

    def start_service(self):
        if not self.running:
            command = self.command_var.get().strip()
            
            # Check if it's a full path to an executable
            is_executable = os.path.isfile(command) and os.access(command, os.X_OK)
            
            # If not a full path, check if command exists in PATH
            if not is_executable and not self.check_command_exists(command):
                self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: Command '{command}' not found")
                self.add_to_log("Please check if OpenWebUI is installed correctly or specify the full path to the executable")
                return
            
            try:
                cmd = f"{command} serve"
                self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing: {cmd}")
                
                # Use shell=True to execute the command as you would in the terminal
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    shell=True  # This is important to use your shell's PATH
                )
                
                self.running = True
                self.status_var.set("Status: Running")
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                
                # Start thread to read output
                threading.Thread(target=self.read_output, daemon=True).start()
                
                self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OpenWebUI service started")
            except Exception as e:
                self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error starting service: {str(e)}")
    
    def stop_service(self):
        if self.running and self.process:
            try:
                # Check if process is still running before trying to terminate
                if self.process.poll() is None:
                    # Send terminate signal to process
                    if hasattr(signal, 'SIGTERM'):
                        try:
                            os.kill(self.process.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            # Process already terminated
                            pass
                    else:
                        self.process.terminate()
                
                    # Give it some time to terminate gracefully
                    for _ in range(5):
                        if self.process.poll() is not None:
                            break
                        time.sleep(0.5)
                    
                    # Force kill if still running
                    if self.process.poll() is None:
                        self.process.kill()
                
                self.running = False
                self.status_var.set("Status: Not Running")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.proc_mem_var.set("N/A")
                
                self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] OpenWebUI service stopped")
            except Exception as e:
                self.add_to_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error stopping service: {str(e)}")
                # Ensure UI is updated even if an error occurs
                self.running = False
                self.status_var.set("Status: Error")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
    
    def read_output(self):
        """Read the output from the process in a separate thread."""
        for line in iter(self.process.stdout.readline, ''):
            if line:
                self.output_queue.put(line)
            else:
                break
        
        # Process ended
        if self.running:
            self.running = False
            self.output_queue.put(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Process exited")
            self.root.after(0, self.update_status_stopped)
    
    def update_status_stopped(self):
        self.status_var.set("Status: Not Running")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.proc_mem_var.set("N/A")
    
    def check_queue(self):
        """Check if there's any output in the queue and update the log."""
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.add_to_log(line)
                self.output_queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Schedule to run again
            self.root.after(100, self.check_queue)
    
    def add_to_log(self, text):
        """Add text to the log widget."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)  # Scroll to the end
        self.log_text.config(state=tk.DISABLED)
    
    def get_mac_gpu_info(self):
        """Get GPU information on macOS systems"""
        try:
            # Run system_profiler to get GPU information
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            
            # Parse the output to extract GPU info
            gpu_info = {"name": "Unknown GPU", "metal": False}
            metal_found = False
            current_section = None
            
            lines = output.splitlines()
            for line in lines:
                line = line.strip()
                
                # Check for graphics card section
                if "Chipset Model:" in line:
                    gpu_info["name"] = line.split(":", 1)[1].strip()
                
                # Check for Metal support
                if "Metal:" in line:
                    metal_support = line.split(":", 1)[1].strip()
                    if "supported" in metal_support.lower():
                        gpu_info["metal"] = True
                
                # Get VRAM if available
                if "VRAM" in line and ":" in line:
                    try:
                        vram_text = line.split(":", 1)[1].strip()
                        # Extract just the number
                        vram_mb = int(''.join(filter(str.isdigit, vram_text)))
                        gpu_info["vram"] = vram_mb
                    except:
                        pass
            
            return gpu_info
        except Exception as e:
            print(f"Error getting Mac GPU info: {e}")
            return None
    
    def update_resources(self):
        """Update system resource information."""
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.cpu_var.set(f"{cpu_percent:.1f}%")
        self.cpu_progress['value'] = cpu_percent
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_var.set(f"{memory_percent:.1f}% ({self.format_bytes(memory.used)})")
        self.memory_progress['value'] = memory_percent
        
        # GPU usage - handle different platforms
        if IS_MACOS:
            # Apple Silicon/Mac GPU monitoring
            try:
                mac_gpu = self.get_mac_gpu_info()
                if mac_gpu:
                    self.gpu_var.set(f"Active: {mac_gpu.get('name', 'Unknown GPU')}")
                    self.gpu_progress['value'] = 50  # We don't have usage percentage on Mac
                    
                    # Show VRAM if available, otherwise show Metal support
                    if "vram" in mac_gpu:
                        self.gpu_memory_var.set(f"VRAM: {mac_gpu['vram']} MB")
                        self.gpu_memory_progress['value'] = 50  # We don't have usage percentage
                    else:
                        metal_support = "Yes" if mac_gpu.get('metal', False) else "No"
                        self.gpu_memory_var.set(f"Metal Support: {metal_support}")
                        self.gpu_memory_progress['value'] = 100 if mac_gpu.get('metal', False) else 0
                else:
                    self.gpu_var.set("No Mac GPU info available")
                    self.gpu_memory_var.set("No Mac GPU info available")
                    self.gpu_progress['value'] = 0
                    self.gpu_memory_progress['value'] = 0
            except Exception as e:
                self.gpu_var.set(f"Error: {str(e)}")
                self.gpu_memory_var.set("Error retrieving Mac GPU info")
                self.gpu_progress['value'] = 0
                self.gpu_memory_progress['value'] = 0
        elif GPU_AVAILABLE:
            # NVIDIA GPU monitoring via GPUtil
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use the first GPU
                    gpu_util = gpu.load * 100  # Convert to percentage
                    gpu_memory_used = gpu.memoryUsed
                    gpu_memory_total = gpu.memoryTotal
                    gpu_memory_percent = (gpu_memory_used / gpu_memory_total) * 100
                    
                    self.gpu_var.set(f"{gpu_util:.1f}% ({gpu.name})")
                    self.gpu_progress['value'] = gpu_util
                    
                    self.gpu_memory_var.set(f"{gpu_memory_percent:.1f}% ({gpu_memory_used:.0f} MB / {gpu_memory_total:.0f} MB)")
                    self.gpu_memory_progress['value'] = gpu_memory_percent
                else:
                    self.gpu_var.set("No GPU detected")
                    self.gpu_memory_var.set("No GPU detected")
                    self.gpu_progress['value'] = 0
                    self.gpu_memory_progress['value'] = 0
            except Exception as e:
                self.gpu_var.set(f"Error: {str(e)}")
                self.gpu_memory_var.set("Error")
                self.gpu_progress['value'] = 0
                self.gpu_memory_progress['value'] = 0
        else:
            # No GPU monitoring available
            if IS_MACOS:
                self.gpu_var.set("Error accessing Mac GPU")
                self.gpu_memory_var.set("Check permissions")
            else:
                self.gpu_var.set("GPUtil not installed")
                self.gpu_memory_var.set("Install GPUtil with: pip install gputil")
            
            self.gpu_progress['value'] = 0
            self.gpu_memory_progress['value'] = 0
        
        # Process memory if running
        if self.running and self.process and self.process.poll() is None:
            try:
                proc = psutil.Process(self.process.pid)
                proc_memory = proc.memory_info().rss
                self.proc_mem_var.set(self.format_bytes(proc_memory))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.proc_mem_var.set("N/A")
        
        # Schedule the next update
        self.root.after(1000, self.update_resources)  # Changed from 2000 to 1000 milliseconds
    
    def format_bytes(self, bytes):
        """Format bytes to a human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} PB"

if __name__ == "__main__":
    root = tk.Tk()
    app = OpenWebUIController(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (
        app.stop_service() if app.running else None, 
        app.stop_ollama() if app.ollama_running else None,
        root.destroy()
    ))
    root.mainloop()
