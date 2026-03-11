#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""부루마블 스타일 보드게임"""

import tkinter as tk
from tkinter import messagebox, filedialog
import random
import os
import sys
import traceback
import math


def load_questions(filepath):
    questions = []
    if not os.path.exists(filepath):
        return questions
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='cp949') as f:
                content = f.read()
        except Exception:
            return questions
    blocks = content.strip().split('\n\n')
    for block in blocks:
        lines = block.strip().split('\n')
        q_text = ""
        a_text = ""
        for line in lines:
            line = line.strip()
            if line.startswith('문제:') or line.startswith('문제 :'):
                q_text = line.split(':', 1)[1].strip()
            elif line.startswith('정답:') or line.startswith('정답 :'):
                a_text = line.split(':', 1)[1].strip()
        if q_text:
            questions.append({'question': q_text, 'answer': a_text})
    return questions


PLAYER_COLORS = [
    '#e74c3c', '#3498db', '#2ecc71', '#f39c12',
    '#9b59b6', '#1abc9c', '#e67e22', '#e91e63',
    '#00bcd4', '#8bc34a', '#ff5722', '#607d8b',
    '#795548', '#cddc39', '#ff9800', '#673ab7',
]

def get_player_color(idx):
    return PLAYER_COLORS[idx % len(PLAYER_COLORS)]

FONT_NAME = 'Malgun Gothic' if sys.platform == 'win32' else 'sans-serif'

GOLDEN_KEY_EVENTS = [
    "앞으로 3칸 이동!",
    "뒤로 2칸 이동!",
    "한 턴 쉬기!",
    "주사위를 한 번 더 굴릴 수 있는 보너스 턴!",
    "출발지로 돌아가기!",
    "앞으로 5칸 이동!",
    "뒤로 3칸 이동!",
    "행운의 칸! 원하는 칸으로 이동하세요.",
    "다음 문제 칸을 건너뜁니다!",
    "모든 플레이어가 이 칸으로 이동!",
]
GOLDEN_KEY_POPUP_DELAY_MS = 300


# ─── 주사위 면 그리기 (캔버스에 직접) ───
DICE_DOTS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5), (0.25, 0.75), (0.75, 0.75)],
}

def draw_dice_face(canvas, cx, cy, size, value, tag='dice'):
    """캔버스에 주사위 면을 그린다"""
    half = size / 2
    r = size * 0.12  # 둥근 모서리
    x1, y1 = cx - half, cy - half
    x2, y2 = cx + half, cy + half

    # 둥근 사각형 배경
    canvas.create_rectangle(x1 + 2, y1 + 2, x2 + 2, y2 + 2, fill='#888888', outline='', tags=tag)  # 그림자
    canvas.create_rectangle(x1, y1, x2, y2, fill='#ffffff', outline='#333333', width=2, tags=tag)

    # 점 (7 이상이면 숫자로 표시)
    if 1 <= value <= 6:
        dots = DICE_DOTS[value]
        dot_r = size * 0.09
        for dx, dy in dots:
            px = x1 + dx * size
            py = y1 + dy * size
            canvas.create_oval(px - dot_r, py - dot_r, px + dot_r, py + dot_r,
                               fill='#333333', outline='', tags=tag)
    else:
        canvas.create_text(cx, cy, text=str(value), font=(FONT_NAME, int(size * 0.4), 'bold'),
                           fill='#333333', tags=tag)


# ─── 보드 좌표 계산 ───
def calc_board_positions(total_cells, board_x, board_y, board_w, board_h, max_cell_size=200):
    if total_cells < 4:
        total_cells = 4

    ratio = board_w / board_h if board_h > 0 else 1
    target_sum = (total_cells + 4) / 2
    h_ideal = target_sum * ratio / (1 + ratio)

    h = max(2, round(h_ideal))
    v = max(2, round(target_sum - h_ideal))

    peri = 2 * h + 2 * v - 4
    while peri < total_cells:
        if h <= v:
            h += 1
        else:
            v += 1
        peri = 2 * h + 2 * v - 4

    cw = board_w / h
    ch = board_h / v
    cs = min(cw, ch, max_cell_size)
    cs = max(cs, 15)

    aw = h * cs
    ah = v * cs
    sx = board_x + (board_w - aw) / 2
    sy = board_y + (board_h - ah) / 2

    cells_grid = []
    for c in range(h):
        cells_grid.append((c, 0))
    for r in range(1, v):
        cells_grid.append((h - 1, r))
    for c in range(h - 2, -1, -1):
        cells_grid.append((c, v - 1))
    for r in range(v - 2, 0, -1):
        cells_grid.append((0, r))

    positions = []
    for col, row in cells_grid[:total_cells]:
        positions.append((sx + col * cs, sy + row * cs, cs, cs))

    return positions


# ─── 설정 다이얼로그 ───
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_settings):
        super().__init__(parent)
        self.title("게임 설정")
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        s = current_settings

        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill='both', expand=True)

        fields = [
            ("플레이어 수:", 'players', 10),
            ("칸 개수 (최소 4):", 'cells', 10),
            ("문제 칸 번호 (쉼표 구분):", 'question_cells_str', 20),
            ("황금 열쇠 칸 번호 (쉼표 구분):", 'golden_key_cells_str', 20),
            ("주사위 최대값:", 'dice_max', 10),
            ("목표 바퀴 (0=무제한):", 'target_laps', 10),
            ("보드 제목 (윗줄):", 'board_title', 15),
            ("보드 제목 (아랫줄):", 'board_subtitle', 15),
        ]

        self.vars = {}
        for i, (label, key, w) in enumerate(fields):
            tk.Label(frame, text=label, font=(FONT_NAME, 10)).grid(row=i, column=0, sticky='w', pady=4)
            if key == 'question_cells_str':
                val = ','.join(str(x) for x in s.get('question_cells', [3, 7, 11, 15]))
            elif key == 'golden_key_cells_str':
                val = ','.join(str(x) for x in s.get('golden_key_cells', []))
            else:
                val = str(s.get(key, ''))
            sv = tk.StringVar(value=val)
            tk.Entry(frame, textvariable=sv, width=w).grid(row=i, column=1, sticky='w', pady=4)
            self.vars[key] = sv

        row = len(fields)
        tk.Label(frame, text="문제 파일:", font=(FONT_NAME, 10)).grid(row=row, column=0, sticky='w', pady=4)
        ff = tk.Frame(frame)
        ff.grid(row=row, column=1, sticky='w', pady=4)
        self.var_qfile = tk.StringVar(value=s.get('question_file', 'questions.txt'))
        tk.Entry(ff, textvariable=self.var_qfile, width=25).pack(side='left')
        tk.Button(ff, text="찾기", command=self._browse).pack(side='left', padx=4)

        bf = tk.Frame(frame)
        bf.grid(row=row + 1, column=0, columnspan=2, pady=12)
        tk.Button(bf, text="확인", command=self._ok, width=8).pack(side='left', padx=8)
        tk.Button(bf, text="취소", command=self.destroy, width=8).pack(side='left', padx=8)

        self.transient(parent)
        self.wait_window()

    def _browse(self):
        p = filedialog.askopenfilename(title="문제 파일 선택",
                                        filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")])
        if p:
            self.var_qfile.set(p)

    def _ok(self):
        try:
            players = int(self.vars['players'].get())
            cells = int(self.vars['cells'].get())
            dice_max = int(self.vars['dice_max'].get())
            target_laps = int(self.vars['target_laps'].get())
            if players < 1: raise ValueError("플레이어 수는 1 이상")
            if cells < 4: raise ValueError("칸 개수는 4 이상")
            if cells % 2 != 0: cells += 1
            if dice_max < 1: raise ValueError("주사위 최대값은 1 이상")
            if target_laps < 0: raise ValueError("목표 바퀴는 0 이상")
        except ValueError as e:
            messagebox.showerror("입력 오류", str(e)); return

        qcells_str = self.vars['question_cells_str'].get().strip()
        question_cells = []
        if qcells_str:
            try:
                question_cells = [int(x.strip()) for x in qcells_str.split(',') if x.strip()]
                for qc in question_cells:
                    if qc < 0 or qc >= cells:
                        raise ValueError("문제 칸 번호 " + str(qc) + "는 범위 밖")
            except ValueError as e:
                messagebox.showerror("입력 오류", str(e)); return

        gkstr = self.vars['golden_key_cells_str'].get().strip()
        golden_key_cells = []
        if gkstr:
            try:
                golden_key_cells = [int(x.strip()) for x in gkstr.split(',') if x.strip()]
                for gkc in golden_key_cells:
                    if gkc < 0 or gkc >= cells:
                        raise ValueError("황금 열쇠 칸 번호 " + str(gkc) + "는 범위 밖")
            except ValueError as e:
                messagebox.showerror("입력 오류", str(e)); return

        self.result = {
            'players': players, 'cells': cells, 'question_cells': question_cells,
            'golden_key_cells': golden_key_cells,
            'dice_max': dice_max, 'target_laps': target_laps,
            'question_file': self.var_qfile.get(),
            'board_title': self.vars['board_title'].get(),
            'board_subtitle': self.vars['board_subtitle'].get(),
        }
        self.destroy()


# ─── 메인 앱 ───
class BoardGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("부루마블 보드게임")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        self.settings = {
            'players': 2, 'cells': 20, 'question_cells': [3, 7, 11, 15],
            'golden_key_cells': [5, 13],
            'dice_max': 6, 'target_laps': 3, 'question_file': 'questions.txt',
            'board_title': '부루마블', 'board_subtitle': '보드게임',
        }

        self.player_positions = []
        self.player_laps = []
        self.current_player = 0
        self.dice_result = 0
        self.manual_mode = False
        self.questions = []
        self.used_question_indices = []
        self.winner = None
        self.cell_rects = []
        self.zoom_level = 1.0
        self.dice_animating = False

        self._build_ui()
        self.new_game()

    def _build_ui(self):
        PBG = '#2c2c2c'
        PFG = '#eeeeee'
        BBG = '#444444'
        BFG = '#ffffff'
        BA = '#555555'

        self.canvas = tk.Canvas(self.root, bg='#f5f0e1')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.draw_board())
        self.canvas.bind('<Button-1>', self._on_click)

        # Ctrl+휠 줌
        self.canvas.bind('<Control-MouseWheel>', self._on_zoom)          # Windows
        self.canvas.bind('<Control-Button-4>', self._on_zoom_linux_up)   # Linux
        self.canvas.bind('<Control-Button-5>', self._on_zoom_linux_down) # Linux

        # 패널
        self.panel_visible = True
        self.left_panel = tk.Frame(self.root, bg=PBG, bd=0, highlightthickness=0)
        self.left_panel.place(x=0, y=0, width=240, relheight=1.0)

        self.btn_toggle = tk.Button(self.root, text='<', font=(FONT_NAME, 9),
                                     bg=BBG, fg=BFG, bd=0, activebackground='#666', command=self._toggle_panel)
        self.btn_toggle.place(x=240, y=10, width=24, height=30)

        def btn(parent, text, cmd):
            return tk.Button(parent, text=text, command=cmd, bg=BBG, fg=BFG,
                             activebackground=BA, activeforeground=BFG, font=(FONT_NAME, 10),
                             bd=0, padx=8, pady=4, relief='flat', cursor='hand2')

        def lbl(parent, text, sz=10, bold=False):
            w = 'bold' if bold else 'normal'
            return tk.Label(parent, text=text, bg=PBG, fg=PFG, font=(FONT_NAME, sz, w), anchor='w')

        def sep(parent):
            tk.Frame(parent, bg='#555', height=1).pack(fill='x', padx=8, pady=6)

        px = 8
        btn(self.left_panel, "[설정]", self.open_settings).pack(fill='x', padx=px, pady=(8, 2))
        btn(self.left_panel, "[새 게임]", self.new_game).pack(fill='x', padx=px, pady=(0, 4))
        sep(self.left_panel)

        self.lbl_turn = lbl(self.left_panel, "현재 턴: -", sz=12, bold=True)
        self.lbl_turn.pack(anchor='w', padx=px, pady=(2, 0))
        self.turn_color_cv = tk.Canvas(self.left_panel, width=220, height=8, highlightthickness=0, bg=PBG)
        self.turn_color_cv.pack(anchor='w', padx=px, pady=(2, 4))
        sep(self.left_panel)

        lbl(self.left_panel, "주사위", bold=True).pack(anchor='w', padx=px)
        self.lbl_dice = lbl(self.left_panel, "결과: -", sz=16)
        self.lbl_dice.pack(anchor='w', padx=px, pady=2)
        btn(self.left_panel, "[주사위 굴리기]", self.roll_dice).pack(fill='x', padx=px, pady=2)
        sep(self.left_panel)

        lbl(self.left_panel, "이동", bold=True).pack(anchor='w', padx=px)
        btn(self.left_panel, "[자동 이동]", self.auto_move).pack(fill='x', padx=px, pady=2)
        btn(self.left_panel, "[수동 이동 모드]", self.toggle_manual).pack(fill='x', padx=px, pady=2)
        self.lbl_manual = tk.Label(self.left_panel, text="", bg=PBG, fg='#ff6b6b', font=(FONT_NAME, 9))
        self.lbl_manual.pack(anchor='w', padx=px)
        sep(self.left_panel)

        self.btn_question = btn(self.left_panel, "[문제 출력]", self.show_question)
        self.btn_question.pack(fill='x', padx=px, pady=2)
        self.btn_question.config(state='disabled')
        sep(self.left_panel)

        btn(self.left_panel, "[다음 턴]", self.next_turn).pack(fill='x', padx=px, pady=2)
        sep(self.left_panel)

        lbl(self.left_panel, "바퀴 현황", bold=True).pack(anchor='w', padx=px)
        lc = tk.Frame(self.left_panel, bg=PBG)
        lc.pack(fill='both', expand=True, padx=px, pady=4)
        self.lap_cv = tk.Canvas(lc, highlightthickness=0, bg=PBG)
        lsb = tk.Scrollbar(lc, orient='vertical', command=self.lap_cv.yview)
        self.lap_frame = tk.Frame(self.lap_cv, bg=PBG)
        self.lap_frame.bind('<Configure>', lambda e: self.lap_cv.configure(scrollregion=self.lap_cv.bbox('all')))
        self.lap_cv.create_window((0, 0), window=self.lap_frame, anchor='nw')
        self.lap_cv.configure(yscrollcommand=lsb.set)
        self.lap_cv.pack(side='left', fill='both', expand=True)
        lsb.pack(side='right', fill='y')

        # 줌 라벨
        self.lbl_zoom = tk.Label(self.left_panel, text="줌: 100%", bg=PBG, fg='#aaaaaa', font=(FONT_NAME, 8))
        self.lbl_zoom.pack(anchor='w', padx=px, pady=(0, 4))

    # ─── 줌 ───
    def _on_zoom(self, event):
        if event.delta > 0:
            self.zoom_level = min(3.0, self.zoom_level + 0.1)
        else:
            self.zoom_level = max(0.3, self.zoom_level - 0.1)
        self.lbl_zoom.config(text="줌: " + str(int(self.zoom_level * 100)) + "%")
        self.draw_board()

    def _on_zoom_linux_up(self, event):
        self.zoom_level = min(3.0, self.zoom_level + 0.1)
        self.lbl_zoom.config(text="줌: " + str(int(self.zoom_level * 100)) + "%")
        self.draw_board()

    def _on_zoom_linux_down(self, event):
        self.zoom_level = max(0.3, self.zoom_level - 0.1)
        self.lbl_zoom.config(text="줌: " + str(int(self.zoom_level * 100)) + "%")
        self.draw_board()

    def _toggle_panel(self):
        if self.panel_visible:
            self.left_panel.place_forget()
            self.btn_toggle.place(x=0, y=10, width=24, height=30)
            self.btn_toggle.config(text='>')
            self.panel_visible = False
        else:
            self.left_panel.place(x=0, y=0, width=240, relheight=1.0)
            self.btn_toggle.place(x=240, y=10, width=24, height=30)
            self.btn_toggle.config(text='<')
            self.panel_visible = True
        self.draw_board()

    # ─── 게임 ───
    def new_game(self):
        s = self.settings
        self.player_positions = [0] * s['players']
        self.player_laps = [0] * s['players']
        self.current_player = 0
        self.dice_result = 0
        self.manual_mode = False
        self.winner = None
        self.lbl_manual.config(text="")
        self.questions = load_questions(s['question_file'])
        self.used_question_indices = []
        self._update_turn()
        self._update_laps()
        self._update_dice_label()
        self.btn_question.config(state='disabled')
        self.draw_board()

    def open_settings(self):
        dlg = SettingsDialog(self.root, self.settings)
        if dlg.result:
            self.settings = dlg.result
            self.new_game()

    # ─── 주사위 (애니메이션) ───
    def roll_dice(self):
        if self.winner is not None:
            messagebox.showinfo("게임 종료", "이미 승리한 플레이어가 있습니다. 새 게임을 시작하세요.")
            return
        if self.dice_animating:
            return
        self.dice_animating = True
        self._dice_animate(0)

    def _dice_animate(self, step):
        if step < 12:
            # 랜덤 값으로 빠르게 교체
            temp_val = random.randint(1, self.settings['dice_max'])
            self._draw_dice_center(temp_val)
            delay = 50 + step * 20  # 점점 느려짐
            self.root.after(delay, self._dice_animate, step + 1)
        else:
            # 최종 결과
            self.dice_result = random.randint(1, self.settings['dice_max'])
            self._draw_dice_center(self.dice_result)
            self._update_dice_label()
            self.dice_animating = False

    def _draw_dice_center(self, value):
        """보드판 중앙에 주사위를 그린다"""
        self.canvas.delete('dice')
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        dice_size = min(cw, ch) * 0.12 * self.zoom_level
        dice_size = max(40, min(dice_size, 120))
        draw_dice_face(self.canvas, cw / 2, ch / 2, dice_size, value, tag='dice')

    def _update_dice_label(self):
        if self.dice_result > 0:
            self.lbl_dice.config(text="결과: " + str(self.dice_result))
        else:
            self.lbl_dice.config(text="결과: -")

    # ─── 이동 ───
    def auto_move(self):
        if self.winner is not None or self.dice_animating:
            return
        if self.dice_result == 0:
            messagebox.showinfo("알림", "먼저 주사위를 굴려주세요.")
            return
        p = self.current_player
        new_pos = self.player_positions[p] + self.dice_result
        tc = self.settings['cells']
        if new_pos >= tc:
            self.player_laps[p] += new_pos // tc
            new_pos = new_pos % tc
        self.player_positions[p] = new_pos
        self.dice_result = 0
        self._update_dice_label()
        self._update_laps()
        self._check_cell_action()
        self.draw_board()
        self._check_win(p)

    def toggle_manual(self):
        if self.winner is not None:
            return
        self.manual_mode = not self.manual_mode
        self.lbl_manual.config(text="[수동 모드 ON] 칸을 클릭하세요" if self.manual_mode else "")

    def _on_click(self, event):
        if not self.manual_mode or self.winner is not None:
            return
        clicked = self._find_cell(event.x, event.y)
        if clicked is not None:
            p = self.current_player
            old = self.player_positions[p]
            if clicked < old or (clicked == 0 and old != 0):
                self.player_laps[p] += 1
            self.player_positions[p] = clicked
            self.manual_mode = False
            self.lbl_manual.config(text="")
            self._update_laps()
            self._check_cell_action()
            self.draw_board()
            self._check_win(p)

    def _find_cell(self, mx, my):
        for i, (x, y, w, h) in enumerate(self.cell_rects):
            if x <= mx <= x + w and y <= my <= y + h:
                return i
        return None

    def next_turn(self):
        if self.winner is not None:
            return
        self.current_player = (self.current_player + 1) % self.settings['players']
        self.dice_result = 0
        self.manual_mode = False
        self.lbl_manual.config(text="")
        self._update_turn()
        self._update_dice_label()
        self.btn_question.config(state='disabled')
        self.draw_board()  # 주사위 지우기

    def _check_win(self, pi):
        t = self.settings['target_laps']
        if t > 0 and self.player_laps[pi] >= t:
            self.winner = pi
            self._update_laps()
            self.draw_board()
            messagebox.showinfo("승리!", "플레이어 " + str(pi + 1) + " 이(가) " + str(t) + "바퀴 완주! 승리!")

    def _check_cell_action(self):
        pos = self.player_positions[self.current_player]
        qcells = set(self.settings['question_cells'])
        gkcells = set(self.settings.get('golden_key_cells', []))
        self.btn_question.config(state='normal' if pos in qcells else 'disabled')
        if pos in gkcells:
            self.root.after(GOLDEN_KEY_POPUP_DELAY_MS, self._show_golden_key_event)

    def _show_golden_key_event(self):
        event = random.choice(GOLDEN_KEY_EVENTS)
        win = tk.Toplevel(self.root)
        win.title("황금 열쇠")
        win.geometry("400x220")
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="[ 황금 열쇠 ]", font=(FONT_NAME, 16, 'bold'), fg='#FF8C00').pack(pady=(20, 5))
        tk.Label(win, text=event, font=(FONT_NAME, 12), wraplength=360).pack(padx=20, pady=10)
        tk.Button(win, text="확인", command=win.destroy, width=10).pack(pady=10)

    def show_question(self):
        if not self.questions:
            messagebox.showinfo("알림", "문제 파일이 비어있습니다.")
            return
        avail = [i for i in range(len(self.questions)) if i not in self.used_question_indices]
        if not avail:
            self.used_question_indices = []
            avail = list(range(len(self.questions)))
        idx = random.choice(avail)
        self.used_question_indices.append(idx)
        q = self.questions[idx]

        win = tk.Toplevel(self.root)
        win.title("문제")
        win.geometry("500x320")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="[ 문제 ]", font=(FONT_NAME, 14, 'bold')).pack(pady=(15, 5))
        qt = tk.Text(win, wrap='word', height=4, font=(FONT_NAME, 12))
        qt.pack(padx=20, fill='x')
        qt.insert('1.0', q['question'])
        qt.config(state='disabled')

        af = tk.Frame(win)
        af.pack(pady=10, padx=20, fill='x')
        at = tk.Text(af, wrap='word', height=3, font=(FONT_NAME, 12), bg='#f0f0f0')
        at.insert('1.0', q['answer'])
        at.config(state='disabled')
        vis = [False]

        def toggle():
            if vis[0]:
                at.pack_forget()
                ba.config(text="정답 보기")
                vis[0] = False
            else:
                at.pack(fill='x')
                ba.config(text="정답 숨기기")
                vis[0] = True

        ba = tk.Button(win, text="정답 보기", command=toggle)
        ba.pack(pady=5)
        tk.Button(win, text="닫기", command=win.destroy).pack(pady=5)
        self.btn_question.config(state='disabled')

    # ─── UI 업데이트 ───
    def _update_turn(self):
        p = self.current_player
        self.lbl_turn.config(text="현재 턴: 플레이어 " + str(p + 1))
        self.turn_color_cv.delete('all')
        self.turn_color_cv.create_rectangle(0, 0, 220, 8, fill=get_player_color(p), outline='')

    def _update_laps(self):
        for w in self.lap_frame.winfo_children():
            w.destroy()
        t = self.settings['target_laps']
        PBG, PFG = '#2c2c2c', '#eeeeee'
        for i in range(self.settings['players']):
            col = get_player_color(i)
            r = tk.Frame(self.lap_frame, bg=PBG)
            r.pack(fill='x', pady=1)
            c = tk.Canvas(r, width=14, height=14, highlightthickness=0, bg=PBG)
            c.pack(side='left', padx=(0, 4))
            c.create_rectangle(1, 1, 13, 13, fill=col, outline='#333')
            laps = self.player_laps[i]
            txt = "P" + str(i + 1) + ": " + str(laps) + ("/" + str(t) if t > 0 else "바퀴")
            tk.Label(r, text=txt, font=(FONT_NAME, 10), bg=PBG, fg=PFG).pack(side='left')

    # ─── 보드 그리기 ───
    def draw_board(self):
        self.canvas.delete('all')
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        total = self.settings['cells']
        qcells = set(self.settings['question_cells'])
        gkcells = set(self.settings.get('golden_key_cells', []))

        margin = 15
        max_cs = 200 * self.zoom_level
        self.cell_rects = calc_board_positions(
            total, margin, margin, cw - margin * 2, ch - margin * 2, max_cell_size=max_cs
        )

        # 칸 그리기
        for i, (x, y, w, h) in enumerate(self.cell_rects):
            if i == 0:
                fill, ol = '#FFD700', '#B8860B'
            elif i in qcells:
                fill, ol = '#FF6B6B', '#CC0000'
            elif i in gkcells:
                fill, ol = '#FFB347', '#FF8C00'
            else:
                fill, ol = '#FFFFFF', '#999999'

            self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill, outline=ol, width=2)

            fs_num = max(7, int(w * 0.15))
            self.canvas.create_text(x + w / 2, y + w * 0.18, text=str(i), font=(FONT_NAME, fs_num), fill='#555')

            fs_lbl = max(6, int(w * 0.12))
            if i == 0:
                self.canvas.create_text(x + w / 2, y + h - w * 0.15,
                                         text="출발", font=(FONT_NAME, fs_lbl, 'bold'), fill='#8B4513')
            elif i in qcells:
                self.canvas.create_text(x + w / 2, y + h - w * 0.15,
                                         text="문제", font=(FONT_NAME, fs_lbl, 'bold'), fill='#CC0000')
            elif i in gkcells:
                self.canvas.create_text(x + w / 2, y + h - w * 0.15,
                                         text="황금열쇠", font=(FONT_NAME, fs_lbl, 'bold'), fill='#CC6600')

        # 장기말
        pos_groups = {}
        for pi in range(self.settings['players']):
            pos = self.player_positions[pi]
            if pos not in pos_groups:
                pos_groups[pos] = []
            pos_groups[pos].append(pi)

        for pos, plist in pos_groups.items():
            if pos >= len(self.cell_rects):
                continue
            rx, ry, rw, rh = self.cell_rects[pos]
            cx, cy = rx + rw / 2, ry + rh / 2
            cnt = len(plist)
            pr = min(rw / 4.5, rw * 0.2)

            for j, pi in enumerate(plist):
                ox = (j - (cnt - 1) / 2) * (pr * 1.8)
                px, py = cx + ox, cy + 1
                color = get_player_color(pi)
                self.canvas.create_oval(px - pr, py - pr, px + pr, py + pr,
                                         fill=color, outline='#333', width=2)
                fs = max(7, int(pr * 0.9))
                self.canvas.create_text(px, py, text=str(pi + 1),
                                         font=(FONT_NAME, fs, 'bold'), fill='white')

        # 중앙: 주사위 결과가 있으면 주사위, 없으면 제목
        if self.dice_result > 0:
            self._draw_dice_center(self.dice_result)
        else:
            t1 = self.settings.get('board_title', '부루마블')
            t2 = self.settings.get('board_subtitle', '보드게임')
            fs1 = max(14, int(min(cw, ch) * 0.04 * self.zoom_level))
            fs2 = max(10, int(min(cw, ch) * 0.025 * self.zoom_level))
            if t1:
                self.canvas.create_text(cw / 2, ch / 2 - fs1 * 0.6, text=t1,
                                         font=(FONT_NAME, fs1, 'bold'), fill='#8B7355')
            if t2:
                self.canvas.create_text(cw / 2, ch / 2 + fs2 * 0.8, text=t2,
                                         font=(FONT_NAME, fs2), fill='#A08060')


if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = BoardGameApp(root)
        root.mainloop()
    except Exception as e:
        err = traceback.format_exc()
        lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_log.txt")
        with open(lp, 'w', encoding='utf-8') as f:
            f.write(err)
        print(err)
        input("에러 발생. 엔터를 누르세요...")
