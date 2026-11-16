import os
import shutil
import subprocess
from typing import Dict, Any

class HardwareMonitor:
    @staticmethod
    def get_hardware_info() -> Dict[str, Any]:
        info = {
            "os": "Windows",
            "cpu_count": os.cpu_count() or 4,
            "ram_total_gb": 16.0,
            "ram_available_gb": 10.0,
            "gpu_detected": False,
            "gpu_name": "None",
            "recommended_profile": "BALANCED",
            "recommended_whisper": "base",
        }

        # Check memory via systeminfo or powershell if available
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong

            class MEMORYSTATUS(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', c_ulonglong),
                    ('ullAvailPhys', c_ulonglong),
                    ('ullTotalPageFile', c_ulonglong),
                    ('ullAvailPageFile', c_ulonglong),
                    ('ullTotalVirtual', c_ulonglong),
                    ('ullAvailVirtual', c_ulonglong),
                    ('ullAvailExtendedVirtual', c_ulonglong),
                ]

            stat = MEMORYSTATUS()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUS)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                info["ram_total_gb"] = round(stat.ullTotalPhys / (1024**3), 1)
                info["ram_available_gb"] = round(stat.ullAvailPhys / (1024**3), 1)
        except Exception:
            pass

        # Check GPU via nvidia-smi
        if shutil.which("nvidia-smi"):
            try:
                res = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, timeout=2)
                if res.returncode == 0 and res.stdout.strip():
                    info["gpu_detected"] = True
                    info["gpu_name"] = res.stdout.strip().split("\n")[0]
            except Exception:
                pass

        # Recommendation logic
        if info["ram_total_gb"] <= 8:
            info["recommended_profile"] = "ECO"
            info["recommended_whisper"] = "tiny"
        elif info["ram_total_gb"] >= 32 and info["gpu_detected"]:
            info["recommended_profile"] = "QUALITY"
            info["recommended_whisper"] = "medium"
        else:
            info["recommended_profile"] = "BALANCED"
            info["recommended_whisper"] = "base"

        return info

hardware_monitor = HardwareMonitor()
