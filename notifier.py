"""
notifier.py - إشعارات سطح المكتب (نافذة صغيرة فوق كل النوافذ في ركن الشاشة) + وميض شريط المهام.
بتشتغل حتى لو التطبيق مصغّر. بتُستخدم لإشعار الرسايل ولمكالمات الرنين (قبول / رفض).
"""

import sys
import tkinter as tk

import ui_kit as ui
from ui_kit import C, F


def flash_window(root, count=6):
    """بيخلي أيقونة التطبيق في شريط المهام تومض (ويندوز بس)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        class FLASHWINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT), ("hwnd", wintypes.HWND), ("dwFlags", wintypes.DWORD),
                        ("uCount", wintypes.UINT), ("dwTimeout", wintypes.DWORD)]
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, 0x0000000F | 0x0000000C, count, 0)
        ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
    except Exception:
        pass


def bring_to_front(root):
    try:
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.after(250, lambda: root.attributes("-topmost", False))
        root.focus_force()
    except Exception:
        pass


class Notifier:
    def __init__(self, root):
        self.root = root
        self.popups = []

    def show(self, title, body="", avatar=None, buttons=None, duration=6000, on_click=None, accent=None, key=None):
        """buttons: [(text, bg, callback)]. بترجع الـ popup (فيه .close())."""
        if key:
            for p in list(self.popups):
                if p.key == key:
                    p.close()
        pop = _Popup(self, title, body, avatar, buttons or [], duration, on_click, accent or C.ACCENT, key)
        self.popups.append(pop)
        self.layout()
        return pop

    def layout(self):
        try:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        except tk.TclError:
            return
        y = sh - 70
        for p in reversed(self.popups):
            try:
                p.win.update_idletasks()
                w, h = p.win.winfo_reqwidth(), p.win.winfo_reqheight()
                y -= h
                p.win.geometry(f"+{sw - w - 18}+{y}")
                y -= 10
            except tk.TclError:
                pass

    def remove(self, pop):
        if pop in self.popups:
            self.popups.remove(pop)
        self.layout()

    def close_all(self):
        for p in list(self.popups):
            p.close()


class _Popup:
    def __init__(self, notifier, title, body, avatar, buttons, duration, on_click, accent, key):
        self.n, self.key = notifier, key
        self.job = None
        win = tk.Toplevel(notifier.root)
        self.win = win
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        win.configure(bg=accent)
        card = tk.Frame(win, bg=C.BG_PANEL)
        card.pack(padx=1, pady=1)
        top = tk.Frame(card, bg=C.BG_PANEL)
        top.pack(fill="x", padx=14, pady=(12, 8))
        if avatar is not None:
            tk.Label(top, image=avatar, bg=C.BG_PANEL).pack(side="left", padx=(0, 12))
        col = tk.Frame(top, bg=C.BG_PANEL)
        col.pack(side="left")
        tk.Label(col, text=title, bg=C.BG_PANEL, fg=C.TEXT_PRIMARY, font=F(11, "bold"), anchor="w",
                 wraplength=260, justify="left").pack(fill="x")
        if body:
            tk.Label(col, text=body, bg=C.BG_PANEL, fg=C.TEXT_SECONDARY, font=F(9), anchor="w",
                     wraplength=260, justify="left").pack(fill="x", pady=(2, 0))
        if buttons:
            row = tk.Frame(card, bg=C.BG_PANEL)
            row.pack(fill="x", padx=14, pady=(2, 12))
            for text, bg, cb in buttons:
                b = ui.RoundedButton(row, text, command=lambda cb=cb: self._press(cb), width=118, height=34,
                                     bg=bg, font_size=10)
                b.pack(side="left", padx=(0, 8))
        if on_click:
            for w in ui.walk(card):
                if not isinstance(w, ui.RoundedButton):
                    w.bind("<Button-1>", lambda e: self._press(on_click))
                    w.config(cursor="hand2")
        if duration:
            self.job = win.after(duration, self.close)

    def _press(self, cb):
        self.close()
        try:
            cb()
        except Exception:
            import traceback
            traceback.print_exc()

    def close(self):
        if self.job:
            try:
                self.win.after_cancel(self.job)
            except Exception:
                pass
            self.job = None
        try:
            self.win.destroy()
        except Exception:
            pass
        self.n.remove(self)
