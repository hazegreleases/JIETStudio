import sys
import subprocess
import os
import tkinter as tk
from tkinter import messagebox

def check_requirements():
    """Checks if requirements are installed and prompts to install if missing."""
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        messagebox.showerror("Error", "requirements.txt not found!")
        return False

    missing_packages = []
    with open(req_file, "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for req in requirements:
        package_name = req.split("==")[0].split(">=")[0].strip() # Simple parsing
        if package_name == "tk": continue # tk is usually built-in
        try:
            __import__(package_name.replace("-", "_")) # basic check, might need better mapping for some pkgs
        except ImportError:
            # Try specific mappings if simple import fails
            if package_name == "opencv-python":
                try:
                    import cv2
                except ImportError:
                    missing_packages.append(req)
            elif package_name == "Pillow":
                try:
                    import PIL
                except ImportError:
                    missing_packages.append(req)
            elif package_name == "pyyaml":
                try:
                    import yaml
                except ImportError:
                    missing_packages.append(req)
            else:
                missing_packages.append(req)

    if missing_packages:
        msg = f"The following packages are missing:\n{', '.join(missing_packages)}\n\nDo you want to install them now?"
        if messagebox.askyesno("Missing Requirements", msg):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
                messagebox.showinfo("Success", "Dependencies installed successfully! Restarting app...")
                # Restart the app
                os.execv(sys.executable, ['python'] + sys.argv)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to install dependencies.\n{e}")
                return False
        else:
            messagebox.showwarning("Warning", "App may not function correctly without dependencies.")
            return True # Let them try anyway if they insist
    return True

def check_cuda():
    """Checks if CUDA is available and warns the user if not."""
    try:
        import torch
        if not torch.cuda.is_available():
            messagebox.showwarning(
                "CUDA Not Found", 
                "Pytorch for CUDA is not installed, training and Magic Wand performance can be low."
            )
    except ImportError:
        # If torch isn't installed yet, check_requirements will handle it.
        # We can just return here and let check_requirements do its job.
        pass


def main():
    # We create a root just for the initial checks, then destroy it or use it
    # But since we might restart, we do checks before main loop
    
    # Hide the root window for the check
    root = tk.Tk()
    root.withdraw() 
    
    check_cuda()

    if not check_requirements():
        root.destroy()
        return

    root.destroy()

    # Now import the actual app
    try:
        from app.ui.main_window import MainWindow
        
        app_root = tk.Tk()
        app = MainWindow(app_root)
        app_root.mainloop()
    except ImportError as e:
        # If we just installed, the import might still fail in the same process depending on how python handles it
        # But we attempted a restart execv above.
        # If we are here, it might be a code error or the restart didn't happen/work as expected in that branch.
        # Or we are in the "Let them try anyway" branch.
        messagebox.showerror("Startup Error", f"Could not start application:\n{e}")

if __name__ == "__main__":
    main()
