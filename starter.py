import webview
import subprocess
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Helper for port scanning
def check_port(host, port, timeout=0.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return port, True
    except Exception:
        return port, False

class API:
    def run_ipconfig(self):
        try:
            result = subprocess.check_output("ipconfig", shell=True, text=True)
            return result
        except Exception as e:
            return f"❌ Error running ipconfig: {e}"

    def run_ping(self, target):
        try:
            result = subprocess.check_output(f"ping {target} -n 10", shell=True, text=True)
            return result
        except Exception as e:
            return f"❌ Error running ping: {e}"

    def browse_directory(self):
        window = webview.active_window()
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0]
        return ""

    def run_arp(self):
        try:
            result = subprocess.check_output("arp -a", shell=True, text=True)
            return result
        except Exception as e:
            return f"❌ Error running arp: {e}"

    def run_port_scan(self, target, ports_text):
        try:
            try:
                host_ip = socket.gethostbyname(target)
            except Exception as e:
                return f"❌ Could not resolve host '{target}': {e}"

            ports = set()
            ports_text = (ports_text or "").strip().lower()
            if ports_text in ("", "common"):
                common = [20,21,22,23,25,53,67,68,69,80,110,123,137,138,139,143,161,162,179,389,443,445,514,587,631,993,995,2049,3306,3389,5060,8080]
                ports.update(common)
            else:
                parts = [p.strip() for p in ports_text.split(",") if p.strip()]
                for p in parts:
                    if "-" in p:
                        try:
                            a,b = p.split("-",1)
                            a = int(a); b = int(b)
                            if a > b: a,b = b,a
                            if (b - a) > 2000:
                                return "❌ Range too large. Limit ranges to 2000 ports at most."
                            ports.update(range(a, b+1))
                        except:
                            return f"❌ Invalid range: {p}"
                    else:
                        try:
                            ports.add(int(p))
                        except:
                            return f"❌ Invalid port: {p}"

            ports = sorted([p for p in ports if 1 <= p <= 65535])
            if not ports:
                return "❌ No valid ports parsed."

            out_lines = []
            out_lines.append(f"Port scan of {target} ({host_ip})")
            out_lines.append(f"Ports checked: {len(ports)}")
            out_lines.append(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            out_lines.append("---------------------------------------------------")

            open_ports = []
            timeout = 0.5
            max_workers = min(200, len(ports))
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = { ex.submit(check_port, host_ip, p, timeout): p for p in ports }
                for fut in as_completed(futures):
                    p, ok = fut.result()
                    if ok:
                        open_ports.append(p)

            if open_ports:
                open_ports_sorted = sorted(open_ports)
                for p in open_ports_sorted:
                    out_lines.append(f"[OPEN]  Port {p}")
            else:
                out_lines.append("No open ports found.")

            out_lines.append("---------------------------------------------------")
            out_lines.append(f"Found open ports: {len(open_ports)}")
            if open_ports:
                out_lines.append("List: " + ", ".join(str(p) for p in sorted(open_ports)))
            out_lines.append(f"End time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return "\n".join(out_lines)
        except Exception as e:
            return f"❌ Error during port scan: {e}"

file_path = "index.html"

if __name__ == '__main__':
    api = API()
    webview.create_window(
        "NetworkMenu v2.0",
        file_path,
        width=800,
        height=600,
        resizable=False,
        js_api=api
    )
    webview.start()
