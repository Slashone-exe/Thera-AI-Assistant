import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import psutil
import sys
import re
import os
import signal

# Updated import to match the new refactored controller structure
from tools.ps_controller import APP_EXECUTABLES

class LaraTesterUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Lara AI - Full System & Lifecycle Tester")
        self.root.geometry("1100x750")

        self.process = None
        self.results = []
        self.output_buffer = []  # Used to capture output for assertions
        self.processed_apps = set()
        self.test_running = False
        self.stop_requested = False

        self.create_widgets()

    # ------------------ UI ------------------

    def create_widgets(self):
        # Control frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        tk.Button(
            control_frame,
            text="1. Test Core Features (Safe)",
            bg="#007ACC",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.start_core_test
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            control_frame,
            text="2. Test All Installed Apps (Intensive)",
            bg="green",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.start_app_lifecycle_test
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            control_frame,
            text="Stop Test",
            bg="red",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.stop_test
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            control_frame,
            text="Clear Output",
            bg="gray",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.clear_output
        ).pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(self.root, text="Status: Idle", font=("Arial", 12))
        self.status.pack()

        # Progress bar frame
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_label = tk.Label(self.progress_frame, text="Progress: 0/0", font=("Arial", 10))
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = tk.Canvas(self.progress_frame, height=20, bg='lightgray')
        self.progress_bar.pack(fill=tk.X, expand=True, padx=(10, 0))
        
        self.progress_rect = None

        self.output_area = scrolledtext.ScrolledText(
            self.root, 
            width=130, 
            height=28,
            font=("Consolas", 9),
            bg="#1E1E1E",
            fg="#D4D4D4"
        )
        self.output_area.pack(padx=10, pady=5)

        # Summary frame
        summary_frame = tk.Frame(self.root)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.summary = tk.Label(summary_frame, text="Summary:", font=("Arial", 11, "bold"))
        self.summary.pack(side=tk.LEFT)
        
        self.save_button = tk.Button(
            summary_frame,
            text="Save Results to File",
            command=self.save_results,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.RIGHT)

    def log(self, text, is_system=False):
        """Log text to output area with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "⚙️ " if is_system else ""
        self.output_area.insert(tk.END, f"[{timestamp}] {prefix}{text}\n")
        self.output_area.see(tk.END)
        self.root.update()

    def clear_output(self):
        """Clear the output area"""
        self.output_area.delete(1.0, tk.END)
        self.results = []
        self.summary.config(text="Summary:")

    def update_progress(self, current, total):
        """Update progress bar"""
        self.progress_label.config(text=f"Progress: {current}/{total}")
        
        if self.progress_rect:
            self.progress_bar.delete(self.progress_rect)
        
        if total > 0:
            width = int((current / total) * (self.progress_bar.winfo_width() - 10))
            if width > 0:
                self.progress_rect = self.progress_bar.create_rectangle(
                    5, 3, width + 5, 17, fill='#4CAF50', outline=''
                )
        self.root.update()

    def stop_test(self):
        """Stop the running test"""
        if self.test_running:
            self.stop_requested = True
            self.log("\n⚠️ Stop requested. Finishing current operation...", is_system=True)

    # ------------------ Fetch Apps ------------------

    def clean_app_name(self, name):
        name = re.sub(r'\{[^}]+\}\\?', '', name)
        name = re.sub(r'\\[^\\]+$', '', name)
        name = re.sub(r'\s*\([^)]*\)', '', name)
        name = re.sub(r'\s+-\s+.*$', '', name)
        name = re.sub(r'\s+\d+(?:\.\d+)?$', '', name)
        return name.strip()

    def get_installed_apps(self):
        command = 'powershell "Get-StartApps | Select-Object Name,AppID"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        lines = result.stdout.splitlines()
        apps_dict = {}

        for line in lines[3:]:
            if not line.strip(): continue
            parts = line.strip().rsplit(' ', 1)
            if len(parts) == 2:
                name, appid = parts
                if any(protocol in appid.lower() for protocol in ["http", "steam://", "googleplay", "file://", "ms-"]):
                    continue
                cleaned_name = self.clean_app_name(name)
                if len(cleaned_name) < 2 or cleaned_name.lower() in ['microsoft', 'windows']:
                    continue
                if cleaned_name not in apps_dict:
                    apps_dict[cleaned_name] = {'original': name, 'cleaned': cleaned_name, 'appid': appid}

        apps = list(apps_dict.values())
        self.log(f"📱 Found {len(apps)} unique apps to test", is_system=True)
        return apps

    # ------------------ Process Detection ------------------

    def is_process_running(self, app_info):
        app_name = app_info['cleaned']
        app_original = app_info['original']
        keywords = app_name.lower().split()
        
        for process in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                process_name = process.info['name'] or ""
                process_exe = process.info['exe'] or ""
                process_cmd = ' '.join(process.info['cmdline'] or [])
                process_text = f"{process_name} {process_exe} {process_cmd}".lower()
                
                if all(keyword in process_text for keyword in keywords): return True
                if app_name.lower() in process_name.lower(): return True
                if app_original.lower() in process_name.lower(): return True
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return False

    # ------------------ Lara Initialization ------------------

    def start_lara_process(self):
        """Initializes the Lara subprocess"""
        self.status.config(text="Status: Starting Lara...")
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'
            
            # Ensure we are calling the refactored script
            self.process = subprocess.Popen(
                [sys.executable, "lara.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            reader_thread = threading.Thread(target=self.read_output, daemon=True)
            reader_thread.start()
            
            time.sleep(4) # Wait for preload
            return True
        except Exception as e:
            self.log(f"❌ Failed to start Lara: {e}", is_system=True)
            return False

    def read_output(self):
        """Read output from Lara process and store in buffer for assertions"""
        while self.process and self.process.poll() is None and not self.stop_requested:
            try:
                line = self.process.stdout.readline()
                if line:
                    clean_line = line.strip()
                    if clean_line:
                        # Append to buffer for test assertions
                        self.output_buffer.append(clean_line)
                        # Print to UI if it's not a generic prompt
                        if not any(skip in clean_line for skip in ["You:", "Lara: Ready!"]):
                            self.log(f"🤖 {clean_line}")
            except:
                break

    def terminate_lara(self):
        """Terminate Lara gracefully"""
        try:
            self.process.stdin.write("exit\n")
            self.process.stdin.flush()
            time.sleep(1)
            parent = psutil.Process(self.process.pid)
            for child in parent.children(recursive=True):
                try: child.terminate()
                except: pass
            parent.terminate()
        except:
            pass

    # ------------------ CORE FEATURES TEST SUITE ------------------

    def start_core_test(self):
        if self.test_running:
            self.log("⚠️ Test already running!", is_system=True)
            return
            
        self.stop_requested = False
        self.results = []
        self.test_running = True
        self.clear_output()
        threading.Thread(target=self.run_core_test, daemon=True).start()

    def run_core_test(self):
        self.log("\n🧪 STARTING CORE FEATURES TEST SUITE...", is_system=True)
        if not self.start_lara_process():
            self.test_running = False
            return

        # Define the exact features to test
        test_suite = [
            {"name": "Help Menu", "cmd": "help", "expect": ["Lara Commands", "APPLICATION COMMANDS"], "wait": 2},
            {"name": "List Installed Apps", "cmd": "apps", "expect": ["Found", "applications (showing"], "wait": 3},
            {"name": "List Running Apps", "cmd": "list", "expect": ["Running applications", "No applications running"], "wait": 2},
            {"name": "Open Application", "cmd": "open calculator", "expect": ["Opening 'calculator'", "launched", "running"], "wait": 6},
            {"name": "Check App Status", "cmd": "status calculator", "expect": ["is running", "is not running"], "wait": 2},
            {"name": "Close Application", "cmd": "close calculator", "expect": ["Closing 'calculator'", "closed successfully", "not found"], "wait": 4},
            {"name": "Silent Terminal Run", "cmd": "run echo LARA_TEST_OK", "expect": ["LARA_TEST_OK", "Command executed successfully"], "wait": 3},
            {"name": "Search Filesystem", "cmd": "search win.ini", "expect": ["Searching for", "Found", "files found"], "wait": 6},
            {"name": "Schedule Shutdown (Safe)", "cmd": "shutdown /t 9999", "expect": ["System will shutdown", "Executing shutdown"], "wait": 3},
            {"name": "Cancel Shutdown", "cmd": "cancel", "expect": ["Cancelling", "cancelled", "No scheduled shutdown"], "wait": 3},
            {"name": "Invalid Command Handling", "cmd": "unknown_gibberish_123", "expect": ["I don't understand", "Type 'help'"], "wait": 2}
        ]

        passed = 0
        total = len(test_suite)

        for idx, test in enumerate(test_suite, 1):
            if self.stop_requested:
                break
            
            self.log(f"\n[{idx}/{total}] 📌 Testing: {test['name']}")
            self.update_progress(idx, total)
            
            # Clear assertion buffer
            self.output_buffer.clear()
            
            # Execute
            try:
                self.process.stdin.write(f"{test['cmd']}\n")
                self.process.stdin.flush()
                self.log(f"   ➡️ Sent: {test['cmd']}")
            except Exception as e:
                self.log(f"   ❌ Pipeline Error: {e}")
                self.results.append(f"{test['name']} → ❌ CRASH")
                continue

            # Wait for execution and output processing
            time.sleep(test['wait'])
            
            # Evaluate assertions
            joined_output = " ".join(self.output_buffer).lower()
            
            is_pass = any(exp.lower() in joined_output for exp in test['expect'])
            
            if is_pass:
                result_str = "✅ PASS"
                passed += 1
            else:
                result_str = "❌ FAIL (Expected strings not found in output)"
                
            self.log(f"   Result: {result_str}")
            self.results.append(f"[{test['cmd']}] {test['name']} → {result_str}")

        self.terminate_lara()
        
        # Finalize
        self.status.config(text="Status: Completed")
        self.test_running = False
        self.save_button.config(state=tk.NORMAL)

        summary_text = f"\n📊 Core Test Summary: {passed}/{total} Passed"
        self.summary.config(text=summary_text)
        self.save_results_to_file("Core Features Suite", summary_text)
        self.log("\n" + "=" * 60, is_system=True)
        self.log(summary_text, is_system=True)


    # ------------------ APP LIFECYCLE TEST SUITE (Original) ------------------

    def start_app_lifecycle_test(self):
        if self.test_running:
            self.log("⚠️ Test already running!", is_system=True)
            return
            
        self.stop_requested = False
        self.results = []
        self.test_running = True
        self.clear_output()
        threading.Thread(target=self.run_app_test, daemon=True).start()

    def run_app_test(self):
        self.log("\n🧪 STARTING INTENSIVE APP LIFECYCLE TEST...", is_system=True)
        self.status.config(text="Status: Fetching Apps...")
        apps = self.get_installed_apps()

        if not apps:
            self.log("❌ No apps found.", is_system=True)
            self.test_running = False
            return

        if not self.start_lara_process():
            self.test_running = False
            return

        open_pass = 0
        close_pass = 0
        skipped_close = 0
        total = len(apps)

        for idx, app_info in enumerate(apps, 1):
            if self.stop_requested:
                break

            app_name = app_info['original']
            cleaned_name = app_info['cleaned']

            if self.process.poll() is not None:
                self.log("❌ Lara process ended unexpectedly.", is_system=True)
                break

            self.log(f"\n[{idx}/{total}] 📌 Testing App: {cleaned_name}")
            self.update_progress(idx, total)

            # OPEN TEST
            before_open = self.is_process_running(app_info)
            try:
                self.process.stdin.write(f"open {app_name}\n")
                self.process.stdin.flush()
            except Exception:
                continue

            time.sleep(7)
            after_open = self.is_process_running(app_info)

            if after_open and not before_open:
                open_result = "✅ OPEN PASS"
                open_pass += 1
                app_was_opened = True
            elif after_open and before_open:
                open_result = "🔄 OPEN PASS (already running)"
                open_pass += 1
                app_was_opened = True
            else:
                open_result = "❌ OPEN FAIL"
                app_was_opened = False

            self.log(f"   Open Result: {open_result}")

            # CLOSE TEST
            if app_was_opened:
                try:
                    self.process.stdin.write(f"close {app_name}\n")
                    self.process.stdin.flush()
                except Exception:
                    continue

                time.sleep(5)
                after_close = self.is_process_running(app_info)

                if not after_close:
                    close_result = "✅ CLOSE PASS"
                    close_pass += 1
                else:
                    close_result = "❌ CLOSE FAIL"
                
                self.log(f"   Close Result: {close_result}")
            else:
                close_result = "⏭️ CLOSE SKIPPED"
                skipped_close += 1
                self.log(f"   Close Result: {close_result}")

            self.results.append(f"{cleaned_name} → {open_result} | {close_result}")

        self.terminate_lara()
        
        self.status.config(text="Status: Completed")
        self.test_running = False
        self.save_button.config(state=tk.NORMAL)

        summary_text = (f"\n📊 App Lifecycle Summary: Open {open_pass}/{idx} | "
                       f"Close {close_pass}/{idx - skipped_close} (attempted) | "
                       f"Skipped Close: {skipped_close}")
                       
        self.summary.config(text=summary_text)
        self.save_results_to_file("App Lifecycle Suite", summary_text)
        self.log("\n" + "=" * 60, is_system=True)
        self.log(summary_text, is_system=True)

    # ------------------ Reporting ------------------

    def save_results_to_file(self, suite_type, summary_text):
        filename = f"lara_results_{suite_type.replace(' ', '_')}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"LARA AI TEST RESULTS - {suite_type.upper()}\n")
            f.write("=" * 50 + "\n")
            f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Items Tested: {len(self.results)}\n")
            f.write(summary_text + "\n")
            f.write("=" * 50 + "\n\n")
            
            for r in self.results:
                f.write(r + "\n")
        
        self.log(f"📁 Detailed results saved to {filename}", is_system=True)

    def save_results(self):
        if self.results:
            self.save_results_to_file("Manual_Save", "")


if __name__ == "__main__":
    root = tk.Tk()
    app = LaraTesterUI(root)
    
    def on_closing():
        if app.test_running:
            app.stop_test()
            time.sleep(1)
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()