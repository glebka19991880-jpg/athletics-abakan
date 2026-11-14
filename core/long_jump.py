from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from datetime import date

THIN = Side(style="thin", color="000000")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FONT_TITLE = Font(name="Times New Roman", size=11, bold=True)
FONT_NORMAL = Font(name="Times New Roman", size=10)
FONT_SMALL = Font(name="Times New Roman", size=9)
ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
DASH = "—"

# Нормативы для прыжка в длину
LONG_JUMP_STANDARDS = [
    ("МСМК", 7.95), ("МС", 7.60), ("КМС", 6.95), ("I", 6.50),
    ("II", 6.00), ("III", 5.40), ("Iю", 4.80), ("IIю", 4.20), ("IIIю", 3.60),
]

# Очки по местам
PLACE_POINTS = {1: 20, 2: 17, 3: 15, 4: 14, 5: 13, 6: 12, 7: 11, 8: 10, 9: 9, 10: 8, 11: 7, 12: 6, 13: 5, 14: 4, 15: 3, 16: 2}
DEFAULT_POINTS = 1

def calculate_rank(result_m):
    if result_m is None: return DASH
    try: val = float(result_m)
    except: return DASH
    for rank_name, norm in LONG_JUMP_STANDARDS:
        if val >= norm: return rank_name
    return "б/р"

def calculate_place(results):
    valid = [(i, r) for i, r in enumerate(results) if r is not None]
    sorted_valid = sorted(valid, key=lambda x: x[1], reverse=True)
    places = [None] * len(results)
    prev_val = None
    prev_place = 0
    for pos, (idx, val) in enumerate(sorted_valid, start=1):
        if val == prev_val:
            places[idx] = prev_place
        else:
            places[idx] = pos
            prev_place = pos
            prev_val = val
    return places

def _set_borders(ws, cell_range):
    for row in ws[cell_range]:
        for cell in row: cell.border = BORDER

def _merge_and_write(ws, cell_range, value, font=FONT_NORMAL, align=ALIGN_CENTER):
    ws.merge_cells(cell_range)
    first = ws[cell_range.split(":")[0]]
    first.value = value
    first.font = font
    first.alignment = align
    _set_borders(ws, cell_range)

def _fmt_num(v):
    if v is None or v == "": return DASH
    try: return f"{float(v):.2f}".replace(".", ",")
    except: return str(v)

def _fmt_wind(w):
    if w is None or w == "": return DASH
    try:
        val = float(w)
        sign = "+" if val > 0 else ""
        return f"{sign}{val:.1f}".replace(".", ",")
    except: return str(w)

def export_long_jump_protocol(athletes, event_info):
    wb = Workbook()
    ws = wb.active
    ws.title = "длина"

    widths = {"A": 6, "B": 6, "C": 26, "D": 12, "E": 8, "F": 14, "G": 22, "H": 10, "I": 7, "J": 7, "K": 7, "L": 7, "M": 7, "N": 7, "O": 7, "P": 7, "Q": 7, "R": 7, "S": 7, "T": 7, "U": 7, "V": 12, "W": 4, "X": 10, "Y": 22, "Z": 10}
    for col, w in widths.items(): ws.column_dimensions[col].width = w

    _merge_and_write(ws, "A1:Z1", "АДМИНИСТРАЦИЯ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A2:Z2", "УПРАВЛЕНИЕ КУЛЬТУРЫ, МОЛОДЕЖИ И СПОРТА АДМИНИСТРАЦИИ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A3:Z3", "ФЕДЕРАЦИЯ ЛЕГКОЙ АТЛЕТИКИ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A4:Z4", "СПОРТИВНАЯ ШКОЛА ОЛИМПИЙСКОГО РЕЗЕРВА ПО ЛЕГКОЙ АТЛЕТИКЕ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A5:Z5", event_info.get("venue", ""), FONT_NORMAL, ALIGN_LEFT)
    _merge_and_write(ws, "A6:Z6", event_info.get("title", ""), FONT_NORMAL, ALIGN_LEFT)

    rm, re_, rr = event_info.get("rm", ("", "")), event_info.get("re", ("", "")), event_info.get("rr", ("", ""))
    ws["B8"] = "РМ"; ws["C8"] = f"{rm[0]} {rm[1]}"
    ws["B9"] = "РЕ"; ws["C9"] = f"{re_[0]} {re_[1]}"
    ws["B10"] = "РР"; ws["C10"] = f"{rr[0]} {rr[1]}"
    for r in (8, 9, 10):
        ws[f"B{r}"].font = FONT_SMALL; ws[f"C{r}"].font = FONT_SMALL; ws[f"C{r}"].alignment = ALIGN_LEFT

    ws["D8"] = "СТАРТОВЫЙ ПРОТОКОЛ"; ws["D8"].font = FONT_TITLE
    ws["D9"] = event_info.get("gender", "МУЖЧИНЫ"); ws["D9"].font = FONT_TITLE
    ws["D10"] = event_info.get("discipline", "Прыжок в длину"); ws["D10"].font = FONT_TITLE

    _merge_and_write(ws, "S7:U7", "Название этапа", FONT_SMALL); _merge_and_write(ws, "V7:X7", event_info.get("stage", "финальные соревнования"), FONT_SMALL)
    _merge_and_write(ws, "S8:U8", "Дата проведения", FONT_SMALL); _merge_and_write(ws, "V8:X8", str(event_info.get("date", "")), FONT_SMALL)
    _merge_and_write(ws, "S9:U9", "Время", FONT_SMALL); _merge_and_write(ws, "V9:X9", str(event_info.get("time", "")), FONT_SMALL)

    # --- СЧИТАЕМ МЕСТА ---
    results = [a.get("result") for a in athletes]
    places = calculate_place(results)

    # --- ПРИВЯЗЫВАЕМ МЕСТО К КАЖДОМУ СПОРТСМЕНУ ---
    for i, a in enumerate(athletes):
        a["place"] = places[i]

    # --- СОРТИРУЕМ ПО УБЫВАНИЮ РЕЗУЛЬТАТА (1-е место вверх) ---
    athletes.sort(key=lambda x: x.get("result") if x.get("result") is not None else -1, reverse=True)

    headers = ["№ уч.", "№п/п", "Фамилия Имя", "Дата рождения", "Заявл. разряд", "Регион, МО", "Ведомственная принадлежность Организация", "Рез-т квал.", "1", "Ветер", "2", "Ветер", "3", "Ветер", "Ж", "4", "Ветер", "5", "Ветер", "6", "Ветер", "Результат", "", "Выполн. разряд", "тренеры", "Очки и Бонус"]
    for idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=12, column=idx, value=h); cell.font = FONT_SMALL; cell.alignment = ALIGN_CENTER; cell.border = BORDER

    start_row = 13
    for i, a in enumerate(athletes):
        r = start_row + i
        attempts = (a.get("attempts") or []) + [None] * (6 - len(a.get("attempts") or []))
        winds = (a.get("winds") or []) + [None] * (6 - len(a.get("winds") or []))
        result = a.get("result")
        place = a.get("place") # Берем место, которое привязали ранее
        
        row_values = [
            a.get("num", ""), a.get("order", ""), a.get("name", ""), str(a.get("birth", "")), a.get("rank", ""), a.get("region", ""), a.get("org", ""),
            "", 
            _fmt_num(attempts[0]), _fmt_wind(winds[0]), _fmt_num(attempts[1]), _fmt_wind(winds[1]), _fmt_num(attempts[2]), _fmt_wind(winds[2]),
            "", 
            _fmt_num(attempts[3]), _fmt_wind(winds[3]), _fmt_num(attempts[4]), _fmt_wind(winds[4]), _fmt_num(attempts[5]), _fmt_wind(winds[5]),
            _fmt_num(result), "", calculate_rank(result), a.get("coaches", ""), PLACE_POINTS.get(place, DEFAULT_POINTS) if place else DASH,
        ]
        for col, val in enumerate(row_values, start=1):
            cell = ws.cell(row=r, column=col, value=val); cell.font = FONT_NORMAL; cell.alignment = ALIGN_CENTER if col not in (3, 7, 25) else ALIGN_LEFT; cell.border = BORDER

    last_data_row = start_row + len(athletes) - 1 if athletes else start_row
    footer = last_data_row + 2
    ws.cell(row=footer, column=4, value="Рефери ___ ( ________________________________________________________ )").font = FONT_NORMAL
    ws.cell(row=footer+1, column=4, value="Ст. судья ___ ( _____________________________________________________ )").font = FONT_NORMAL
    ws.cell(row=footer+2, column=4, value="Секретарь __( _______________________________________________________ )").font = FONT_NORMAL
    ws.cell(row=footer+4, column=3, value="Главный судья").font = FONT_NORMAL
    ws.cell(row=footer+4, column=5, value=event_info.get("chief_judge", "Ромащенко А.А., СС 1К, Абакан")).font = FONT_NORMAL
    ws.cell(row=footer+6, column=3, value="Главный секретарь").font = FONT_NORMAL
    ws.cell(row=footer+6, column=5, value=event_info.get("chief_secretary", "Скоринова М.А., ССВК, Абакан")).font = FONT_NORMAL

    ws.cell(row=footer+8, column=3, value=f"Дата формирования протокола: {date.today().strftime('%d.%m.%Y')}").font = FONT_SMALL
    ws.cell(row=footer+8, column=12, value=f"Количество участников: {len(athletes)}").font = FONT_SMALL

    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return wb
