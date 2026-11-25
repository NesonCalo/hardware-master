# -*- coding: utf-8 -*-
"""网络流量监控：所有网卡的实时上下行速率、累计流量与链路信息。"""

import time
import threading
import collections
import socket

import psutil


def _kind(name, isup):
    low = name.lower()
    if any(k in low for k in ("wi-fi", "wifi", "wlan", "无线", "802.11")):
        return "wifi"
    if any(k in low for k in ("vEthernet".lower(), "vethernet", "vmware", "virtual", "loopback",
                              "hyper-v", "tap", "tun", "wireguard", "tailscale", "zerotier")):
        return "virtual"
    if any(k in low for k in ("bluetooth", "蓝牙")):
        return "bt"
    return "eth"


def _fmt_mac(addr):
    return addr.upper() if addr else ""


class NetMonitor(object):
    def __init__(self, history_seconds=1800, interval=1.0):
        self.lock = threading.RLock()
        self.interval = interval
        self.history_seconds = history_seconds

        self._prev = {}
        self._prev_ts = time.time()
        self._session = {}
        self._addrs = {}
        self._stats = {}
        self._addr_ts = 0.0
        self._stat_ts = 0.0

        self.hist_all = collections.deque(maxlen=history_seconds)
        self.hist_nic = {}
        self.peak_up = 0.0
        self.peak_down = 0.0
        self._rates = {}

        boot = psutil.net_io_counters()
        self.boot_recv = boot.bytes_recv
        self.boot_sent = boot.bytes_sent
        self.started = time.time()

        self._thread = threading.Thread(target=self._run, name="netmon", daemon=True)
        self._stop = threading.Event()
        self._thread.start()

    def stop(self):
        self._stop.set()

    # ------------------------------------------------------------------
    def _refresh_static(self, now):
        if now - self._addr_ts > 8:
            try:
                self._addrs = psutil.net_if_addrs()
            except Exception:
                self._addrs = {}
            self._addr_ts = now
        if now - self._stat_ts > 5:
            try:
                self._stats = psutil.net_if_stats()
            except Exception:
                self._stats = {}
            self._stat_ts = now

    def _nic_meta(self, name):
        ip = mac = ""
        speed = 0
        isup = False
        try:
            for a in self._addrs.get(name, []):
                if a.family == psutil.AF_LINK and not mac:
                    mac = _fmt_mac(a.address)
                elif a.family == socket.AF_INET and not ip:
                    ip = a.address
        except Exception:
            pass
        st = self._stats.get(name)
        if st is not None:
            try:
                isup = bool(st.isup)
                speed = int(st.speed or 0)
            except Exception:
                pass
        return ip, mac, speed, isup

    def poll(self):
        now = time.time()
        self._refresh_static(now)
        try:
            counters = psutil.net_io_counters(pernic=True)
        except Exception:
            counters = {}

        dt = max(0.2, now - self._prev_ts)
        self._prev_ts = now

        rows = []
        up_total = down_total = 0.0
        for name, c in counters.items():
            prev = self._prev.get(name)
            if prev is None:
                up_rate = down_rate = 0.0
            else:
                up_rate = max(0.0, (c.bytes_sent - prev[0]) / dt)
                down_rate = max(0.0, (c.bytes_recv - prev[1]) / dt)
            self._prev[name] = (c.bytes_sent, c.bytes_recv)
            self._rates[name] = (up_rate, down_rate)

            sess = self._session.get(name)
            if sess is None:
                sess = [c.bytes_sent, c.bytes_recv]
                self._session[name] = sess

            ip, mac, speed, isup = self._nic_meta(name)
            rows.append({
                "n": name,
                "up": round(up_rate, 1),
                "down": round(down_rate, 1),
                "sent": c.bytes_sent,
                "recv": c.bytes_recv,
                "s_sent": c.bytes_sent - sess[0],
                "s_recv": c.bytes_recv - sess[1],
                "speed": speed,
                "isup": isup,
                "ip": ip,
                "mac": mac,
                "kind": _kind(name, isup),
            })
            up_total += up_rate
            down_total += down_rate

        rows.sort(key=lambda r: (r["down"] + r["up"]), reverse=True)

        self.peak_up = max(self.peak_up, up_total)
        self.peak_down = max(self.peak_down, down_total)

        self.hist_all.append((now, round(down_total, 1), round(up_total, 1)))
        for name, (u, d) in self._rates.items():
            dq = self.hist_nic.get(name)
            if dq is None:
                dq = collections.deque(maxlen=self.history_seconds)
                self.hist_nic[name] = dq
            dq.append((now, d, u))

        boot = psutil.net_io_counters()
        sess_down = sum(r["s_recv"] for r in rows)
        sess_up = sum(r["s_sent"] for r in rows)

        return {
            "ts": now,
            "up": round(up_total, 1),
            "down": round(down_total, 1),
            "rows": rows,
            "sess_down": sess_down,
            "sess_up": sess_up,
            "boot_down": boot.bytes_recv,
            "boot_up": boot.bytes_sent,
            "peak_down": round(self.peak_down, 1),
            "peak_up": round(self.peak_up, 1),
            "nic_count": len(rows),
            "uptime": int(now - self.started),
        }

    def _run(self):
        while not self._stop.is_set():
            try:
                self._snap = self.poll()
            except Exception:
                pass
            self._stop.wait(self.interval)

    def get(self):
        snap = getattr(self, "_snap", None)
        if snap is None:
            self._snap = snap = self.poll()
        return snap
