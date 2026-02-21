import threading
import time
import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None
import platform

class ResourceMonitor:
    def __init__(self, interval=1.0, callback=None):
        self.interval = interval
        self.callback = callback
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _monitor_loop(self):
        while self.running:
            stats = self._get_stats()
            if self.callback:
                self.callback(stats)
            time.sleep(self.interval)

    def _get_stats(self):
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        
        gpu_stats = "N/A"
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    # Just take the first GPU for now
                    gpu = gpus[0]
                    gpu_stats = f"{gpu.load * 100:.1f}% ({gpu.memoryUsed:.0f}MB / {gpu.memoryTotal:.0f}MB)"
            except Exception:
                pass
        
        return {
            "cpu": cpu_percent,
            "ram": ram_percent,
            "gpu": gpu_stats
        }

    def get_device_name(self):
        # Basic device detection logic
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return f"GPU: {gpus[0].name}"
            except:
                pass
        
        # Check for Apple Silicon
        if platform.system() == "Darwin" and platform.machine() == "arm64":
             return "MPS (Apple Silicon)"
             
        return f"CPU: {platform.processor()}"
