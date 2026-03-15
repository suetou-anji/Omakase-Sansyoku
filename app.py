import tkinter as tk
from tkinter import messagebox
import random
import json
import os
import io
import platform
import subprocess
import tempfile
import shutil
from PIL import Image

SAVE_FILE = "reference/saved_colors.json"
GENERATED_FILE = "reference/generated_colors.json"

# ================================
# UIデザイン設定 (全面白・角丸かわいい)
# ================================
BG_WHITE = "#FFFFFF"   # 白い背景色
FG_TEXT = "#333333"    # テキストカラー（ダークグレー）

BTN_BG = "#F0F0F0"     # ボタン背景色（ごく薄いグレー）
BTN_HOVER = "#E0E0E0"  # ホバー時の背景色
BTN_ACTIVE = "#D0D0D0" # ボタン押下時

# 削除用のボタン色（目立たせつつも淡いトーンに）
BTN_DEL_BG = "#FFE4E1"
BTN_DEL_HOVER = "#FFC0CB"

FONT_MAIN = ("Meiryo", 11)
FONT_BOLD = ("Meiryo", 11, "bold")
FONT_TITLE = ("Meiryo", 14, "bold")
FONT_RGB = ("Meiryo", 12)

# ================================
# ユーティリティ
# ================================
def copy_image_to_clipboard(img):
    system = platform.system()
    try:
        if system == "Windows":
            import win32clipboard
            import win32con
            output = io.BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            win32clipboard.CloseClipboard()

        elif system == "Darwin":  # macOS
            with tempfile.NamedTemporaryFile(suffix=".tiff", delete=False) as f:
                temp_path = f.name
            img.save(temp_path, "TIFF")
            
            script = f'set the clipboard to (read (POSIX file "{temp_path}") as TIFF picture)'
            subprocess.run(["osascript", "-e", script], check=True)
            os.remove(temp_path)

        elif system == "Linux":
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                temp_path = f.name
            img.save(temp_path, "PNG")
            
            if shutil.which("wl-copy"):
                with open(temp_path, "rb") as f:
                    subprocess.run(["wl-copy", "-t", "image/png"], stdin=f, check=True)
            elif shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png", "-i", temp_path], check=True)
            else:
                messagebox.showerror("エラー", "Linux環境での画像コピーには、'xclip' または 'wl-copy' ツールが必要です。")
            os.remove(temp_path)
            
        else:
            messagebox.showinfo("情報", f"お使いのOS ({system}) の画像コピーには現在対応していません。")
            
    except ImportError:
        messagebox.showerror("エラー", "Windows環境用の拡張モジュール（pywin32）が見つかりません。")
    except Exception as e:
        messagebox.showerror("エラー", f"画像コピー中にエラーが発生しました:\n{e}")

def copy_web_colors(color_set, root_window):
    """WEBカラーコードをクリップボードにコピーする"""
    root_window.clipboard_clear()
    hex_list = [f'#{r:02x}{g:02x}{b:02x}'.upper() for r, g, b in color_set]
    color_text = ", ".join(hex_list)
    root_window.clipboard_append(color_text)

def create_color_image(color_set):
    width = 300
    height = 100
    img = Image.new("RGB", (width, height))
    w = width // 3
    for i, (r, g, b) in enumerate(color_set):
        for x in range(i * w, (i + 1) * w):
            for y in range(height):
                img.putpixel((x, y), (r, g, b))
    return img

def create_color_palette_chip(parent, root_window, color_set):
    """3色が繋がった可愛い角丸パレットチップ"""
    width = 150
    height = 40
    radius = 15
    canvas = tk.Canvas(parent, width=width, height=height, bg=BG_WHITE, highlightthickness=0)
    
    w_third = width / 3
    
    hex_colors = [f'#{r:02x}{g:02x}{b:02x}'.upper() for r, g, b in color_set]
    rgb_texts = [f"RGB({r}, {g}, {b})" for r, g, b in color_set]

    # --- 左（color 0）---
    canvas.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=hex_colors[0], outline="")
    canvas.create_arc(0, height-radius*2, radius*2, height, start=180, extent=90, fill=hex_colors[0], outline="")
    canvas.create_rectangle(radius, 0, w_third, height, fill=hex_colors[0], outline="")
    canvas.create_rectangle(0, radius, radius, height-radius, fill=hex_colors[0], outline="")

    # --- 中央（color 1）---
    canvas.create_rectangle(w_third, 0, w_third*2, height, fill=hex_colors[1], outline="")

    # --- 右（color 2）---
    right = width
    canvas.create_arc(right-radius*2, 0, right, radius*2, start=0, extent=90, fill=hex_colors[2], outline="")
    canvas.create_arc(right-radius*2, height-radius*2, right, height, start=270, extent=90, fill=hex_colors[2], outline="")
    canvas.create_rectangle(w_third*2, 0, right-radius, height, fill=hex_colors[2], outline="")
    canvas.create_rectangle(right-radius, radius, right, height-radius, fill=hex_colors[2], outline="")

    # --- 仕切り線（くっきり見せるための白い線） ---
    canvas.create_line(w_third, 0, w_third, height, fill=BG_WHITE, width=3)
    canvas.create_line(w_third*2, 0, w_third*2, height, fill=BG_WHITE, width=3)

    # --- ツールチップとアクション ---
    tooltip = tk.Toplevel(canvas)
    tooltip.wm_overrideredirect(True)
    tooltip.withdraw()

    tooltip_label = tk.Label(
        tooltip,
        text="",
        bg=BG_WHITE,
        fg=FG_TEXT,
        font=("Meiryo", 9),
        relief="flat",
        highlightbackground="#DDDDDD",
        highlightthickness=1,
        padx=4, pady=2
    )
    tooltip_label.pack()

    def get_color_index(event):
        if event.x < w_third:
            return 0
        elif event.x < w_third * 2:
            return 1
        else:
            return 2

    def on_motion(event):
        idx = get_color_index(event)
        tooltip_label.config(text=rgb_texts[idx])
        x = canvas.winfo_rootx() + event.x + 15
        y = canvas.winfo_rooty() - 30
        tooltip.wm_geometry(f"+{x}+{y}")
        if tooltip.state() == 'withdrawn':
            tooltip.deiconify()

    def on_leave(event):
        tooltip.withdraw()

    def on_right_click(event):
        idx = get_color_index(event)
        root_window.clipboard_clear()
        root_window.clipboard_append(hex_colors[idx])

    canvas.bind("<Motion>", on_motion)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-3>", on_right_click)

    return canvas

# ================================
# カスタム角丸ボタンクラス
# ================================
class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, corner_radius, padding, color, hover_color, active_color, text, font, fg, command=None):
        tk.Canvas.__init__(self, parent, width=width, height=height, bg=BG_WHITE, highlightthickness=0)
        self.command = command
        self.color = color
        self.hover_color = hover_color
        self.active_color = active_color
        self.radius = corner_radius

        self.rect = self._create_rounded_rect(0, 0, width, height, corner_radius, fill=self.color)
        self.text_id = self.create_text(width/2, height/2, text=text, fill=fg, font=font)

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self.configure(cursor="hand2")

    def _create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [
            x1+radius, y1,
            x1+radius, y1,
            x2-radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_press(self, event):
        self.itemconfig(self.rect, fill=self.active_color)

    def _on_release(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)
        if self.command:
            self.command()

    def _on_enter(self, event):
        self.itemconfig(self.rect, fill=self.hover_color)

    def _on_leave(self, event):
        self.itemconfig(self.rect, fill=self.color)

# ================================
# メインアプリケーションクラス
# ================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("おまかせ三色")
        self.geometry("450x550")
        self.configure(bg=BG_WHITE)
        self.resizable(False, False)

        if platform.system() == "Windows" and os.path.exists("icon.ico"):
            self.iconbitmap("icon.ico")

        self.saved_colors = self.load_data(SAVE_FILE)
        self.generated_history = self.load_data(GENERATED_FILE)

        self.color_labels = []
        self.current_set = []

        self.build_ui()
        self.generate_colors()

    def load_data(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_data(self, filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def build_ui(self):
        title_lbl = tk.Label(self, text="ランダム・カラーパレット", font=FONT_TITLE, bg=BG_WHITE, fg=FG_TEXT)
        title_lbl.pack(pady=(25, 15))

        color_container = tk.Frame(self, bg=BG_WHITE, padx=20, pady=20)
        color_container.pack(pady=10)

        for i in range(3):
            frame = tk.Frame(color_container, bg=BG_WHITE)
            frame.pack(pady=5)
            
            color_box = tk.Label(frame, text="", width=25, height=2, font=FONT_RGB, relief="flat", highlightbackground="#EEEEEE", highlightthickness=1)
            color_box.pack()
            self.color_labels.append(color_box)

        btn_frame_1 = tk.Frame(self, bg=BG_WHITE)
        btn_frame_1.pack(pady=(20, 10))

        btn_generate = RoundedButton(btn_frame_1, width=200, height=45, corner_radius=20, padding=0, 
                                     color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE, 
                                     text="新しい色を生成", font=FONT_BOLD, fg=FG_TEXT, command=self.generate_colors)
        btn_generate.pack()

        btn_frame_2 = tk.Frame(self, bg=BG_WHITE)
        btn_frame_2.pack(pady=10)

        btn_save = RoundedButton(btn_frame_2, width=160, height=40, corner_radius=18, padding=0,
                                 color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                 text="このカラーを保存", font=FONT_MAIN, fg=FG_TEXT, command=self.save_current_colors)
        btn_save.pack(side=tk.LEFT, padx=10)

        btn_history = RoundedButton(btn_frame_2, width=160, height=40, corner_radius=18, padding=0,
                                    color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                    text="保存履歴を見る", font=FONT_MAIN, fg=FG_TEXT, command=self.show_saved_history)
        btn_history.pack(side=tk.LEFT, padx=10)

        btn_frame_3 = tk.Frame(self, bg=BG_WHITE)
        btn_frame_3.pack(pady=5)

        btn_gen_history = RoundedButton(btn_frame_3, width=200, height=40, corner_radius=18, padding=0,
                                        color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                        text="生成履歴を見る", font=FONT_MAIN, fg=FG_TEXT, command=self.show_generated_history)
        btn_gen_history.pack()

    def generate_colors(self):
        self.current_set = []
        for i in range(3):
            r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
            hex_color = f'#{r:02x}{g:02x}{b:02x}'.upper()
            
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_fg = "#000000" if brightness > 150 else "#FFFFFF"

            self.color_labels[i].config(bg=hex_color, text=f'RGB({r}, {g}, {b})  {hex_color}', fg=text_fg)
            self.current_set.append((r, g, b))

        self.generated_history.insert(0, self.current_set)
        if len(self.generated_history) > 30:
            self.generated_history.pop()

        self.save_data(GENERATED_FILE, self.generated_history)

    def save_current_colors(self):
        def do_save():
            self.saved_colors.insert(0, self.current_set)
            if len(self.saved_colors) > 30:
                self.saved_colors.pop()
            self.save_data(SAVE_FILE, self.saved_colors)
            if 'confirm_win' in locals() and confirm_win.winfo_exists():
                confirm_win.destroy()

        if len(self.saved_colors) >= 30:
            confirm_win = tk.Toplevel(self)
            confirm_win.title("保存確認")
            confirm_win.configure(bg=BG_WHITE)
            confirm_win.geometry("350x150")
            msg = "保存件数30件を超過します。\n古いデータが消去されますが、保存しますか？"
            tk.Label(confirm_win, text=msg, font=FONT_MAIN, bg=BG_WHITE, fg=FG_TEXT, pady=20).pack()

            btn_frame = tk.Frame(confirm_win, bg=BG_WHITE)
            btn_frame.pack(pady=10)

            yes_btn = RoundedButton(btn_frame, width=100, height=35, corner_radius=15, padding=0,
                                    color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                    text="はい", font=FONT_MAIN, fg=FG_TEXT, command=do_save)
            yes_btn.pack(side=tk.LEFT, padx=10)

            no_btn = RoundedButton(btn_frame, width=100, height=35, corner_radius=15, padding=0,
                                   color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                   text="いいえ", font=FONT_MAIN, fg=FG_TEXT, command=confirm_win.destroy)
            no_btn.pack(side=tk.LEFT, padx=10)
        else:
            do_save()

    def build_history_window(self, title, data_list, is_saved_history=False):
        history_win = tk.Toplevel(self)
        history_win.title(title)
        # 必要なボタンが収まる無駄のない幅に調整
        history_win.geometry("750x550")
        history_win.configure(bg=BG_WHITE)

        title_lbl = tk.Label(history_win, text=f"■ {title} ■", font=FONT_TITLE, bg=BG_WHITE, fg=FG_TEXT)
        title_lbl.pack(pady=(15, 5))

        # --- 全消去ボタン（保存履歴の場合のみ） ---
        if is_saved_history:
            top_btn_frame = tk.Frame(history_win, bg=BG_WHITE)
            top_btn_frame.pack(pady=(0, 10))

            def delete_all():
                ans = messagebox.askyesno("全消去の確認", "保存履歴がすべて消去されますがよろしかったですか？", parent=history_win)
                if ans:
                    self.saved_colors.clear()
                    self.save_data(SAVE_FILE, self.saved_colors)
                    history_win.destroy()
                    self.show_saved_history() # リフレッシュ

            btn_delete_all = RoundedButton(top_btn_frame, width=200, height=35, corner_radius=15, padding=0,
                                          color=BTN_DEL_BG, hover_color=BTN_DEL_HOVER, active_color=BTN_ACTIVE,
                                          text="保存履歴をすべて消去する", font=("Meiryo", 10, "bold"), fg=FG_TEXT, command=delete_all)
            btn_delete_all.pack()

        # スクロールエリア
        container = tk.Frame(history_win, bg=BG_WHITE)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(container, bg=BG_WHITE, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_WHITE)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        iroha_labels = list("いろはにほへとちりぬるをわかよたれそつねならむうゐのおくやま")

        for i, color_set in enumerate(data_list):
            if is_saved_history:
                label_char = iroha_labels[i] if i < len(iroha_labels) else f"{i+1}"
            else:
                label_char = f"{i+1}"

            row = tk.Frame(scroll_frame, bg=BG_WHITE)
            row.pack(fill="x", pady=10, padx=5)

            # 番号 / いろは
            tk.Label(row, text=label_char, width=3, font=FONT_BOLD, bg=BG_WHITE, fg=FG_TEXT).pack(side=tk.LEFT)

            # カラーチップ（3色繋がったパレット型）
            chips_frame = tk.Frame(row, bg=BG_WHITE)
            chips_frame.pack(side=tk.LEFT, padx=10)

            palette_chip = create_color_palette_chip(chips_frame, self, color_set)
            palette_chip.pack(side=tk.LEFT, pady=2)

            # ボタン群
            actions_frame = tk.Frame(row, bg=BG_WHITE)
            actions_frame.pack(side=tk.RIGHT, padx=5)

            if not is_saved_history:
                # 生成履歴の場合にのみ、保存ボタンを表示
                def make_save_cmd(cs=color_set):
                    return lambda: self.save_specific_colors(cs)
                btn_save = RoundedButton(actions_frame, width=60, height=35, corner_radius=15, padding=0,
                                         color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                         text="保存", font=("Meiryo", 10), fg=FG_TEXT, command=make_save_cmd())
                btn_save.pack(side=tk.LEFT, padx=5)

            # 画像コピーボタン
            btn_copy_img = RoundedButton(actions_frame, width=110, height=35, corner_radius=15, padding=0,
                                         color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                         text="画像コピー", font=("Meiryo", 10), fg=FG_TEXT, 
                                         command=lambda cs=color_set: copy_image_to_clipboard(create_color_image(cs)))
            btn_copy_img.pack(side=tk.LEFT, padx=4)

            # WEBカラーコピーボタン
            btn_copy_hex = RoundedButton(actions_frame, width=140, height=35, corner_radius=15, padding=0,
                                         color=BTN_BG, hover_color=BTN_HOVER, active_color=BTN_ACTIVE,
                                         text="WEBカラーコピー", font=("Meiryo", 10), fg=FG_TEXT, 
                                         command=lambda cs=color_set: copy_web_colors(cs, self))
            btn_copy_hex.pack(side=tk.LEFT, padx=4)

            if is_saved_history:
                # この履歴を削除ボタン
                def make_delete_cmd(index=i):
                    def do_delete():
                        self.saved_colors.pop(index)
                        self.save_data(SAVE_FILE, self.saved_colors)
                        history_win.destroy()
                        self.show_saved_history() # リフレッシュ
                    return do_delete
                
                btn_delete_one = RoundedButton(actions_frame, width=150, height=35, corner_radius=15, padding=0,
                                              color=BTN_DEL_BG, hover_color=BTN_DEL_HOVER, active_color=BTN_ACTIVE,
                                              text="この保存履歴を削除", font=("Meiryo", 10), fg=FG_TEXT,
                                              command=make_delete_cmd())
                btn_delete_one.pack(side=tk.LEFT, padx=4)

            # 区切り線
            sep = tk.Frame(scroll_frame, height=1, bg="#EAEAEA")
            sep.pack(fill="x", padx=10, pady=(5,0))

    def save_specific_colors(self, color_set):
        self.saved_colors.insert(0, color_set)
        if len(self.saved_colors) > 30:
            self.saved_colors.pop()
        self.save_data(SAVE_FILE, self.saved_colors)

    def show_saved_history(self):
        self.build_history_window("保存履歴", self.saved_colors, is_saved_history=True)

    def show_generated_history(self):
        self.build_history_window("生成履歴", self.generated_history, is_saved_history=False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
