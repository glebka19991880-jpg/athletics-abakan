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

# СЛОВАРЬ НОРМАТИВОВ: вид -> пол -> список нормативов
STANDARDS = {
    "длина": {
        "м": [("МСМК", 7.95), ("МС", 7.60), ("КМС", 6.95), ("I", 6.50), ("II", 6.00), ("III", 5.40), ("Iю", 4.80), ("IIю", 4.20), ("IIIю", 3.60)],
        "ж": [("МСМК", 6.70), ("МС", 6.30), ("КМС", 5.60), ("I", 5.20), ("II", 4.80), ("III", 4.30), ("Iю", 3.80), ("IIю", 3.30), ("IIIю", 2.80)]
    },
    "высота": {
        "м": [("МСМК", 2.27), ("МС", 2.15), ("КМС", 2.03), ("I", 1.90), ("II", 1.75), ("III", 1.60), ("Iю", 1.50), ("IIю", 1.40), ("IIIю", 1.30)],
        "ж": [("МСМК", 1.94), ("МС", 1.84), ("КМС", 1.73), ("I", 1.63), ("II", 1.53), ("III", 1.43), ("Iю", 1.33), ("IIю", 1.23), ("IIIю", 1.13)]
    },
    "тройной": {
        "м": [("МСМК", 16.50), ("МС", 15.80), ("КМС", 14.50), ("I", 13.50), ("II", 12.50), ("III", 11.50), ("Iю", 10.50), ("IIю", 9.50), ("IIIю", 8.50)],
        "ж": [("МСМК", 14.00), ("МС", 13.20), ("КМС", 12.00), ("I", 11.20), ("II", 10.40), ("III", 9.60), ("Iю", 8.80), ("IIю", 8.00), ("IIIю", 7.20)]
    },
    "ядро": {
        "м": [("МСМК", 20.50), ("МС", 17.50), ("КМС", 15.60), ("I", 14.00), ("II", 12.00), ("III", 10.00), ("Iю", 8.00), ("IIю", 7.00), ("IIIю", 6.00)],
        "ж": [("МСМК", 17.00), ("МС", 15.00), ("КМС", 13.50), ("I", 12.00), ("II", 10.50), ("III", 8.50), ("Iю", 7.00), ("IIю", 6.00), ("IIIю", 5.00)]
    }
}

PLACE_POINTS = {
    1: 20, 2: 17, 3: 15, 4: 14, 5: 13, 6: 12, 7: 11, 8: 10,
    9: 9, 10: 8, 11: 7, 12: 6, 13: 5, 14: 4, 15: 3, 16: 2,
}
DEFAULT_POINTS = 1

def calculate_rank(result_m, discipline_name, gender="м"):
    if result_m is None or result_m == "" or result_m == 0.0 or result_m == -1.0:
        return DASH
    try:
        val = float(result_m)
    except (TypeError, ValueError):
        return DASH
        
    discipline_standards = STANDARDS.get(discipline_name.lower(), {}).get(gender.lower(), STANDARDS["длина"]["м"])
    
    for rank_name, norm in discipline_standards:
        if val >= norm:
            return rank_name
    return "б/р"

def calculate_place(results):
    valid = [(i, r) for i, r in enumerate(results) if r is not None and r != "" and r != 0.0 and r != -1.0]
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

def calculate_points(place):
    if place is None:
        return DASH
    return PLACE_POINTS.get(place, DEFAULT_POINTS)

def _set_borders(ws, cell_range):
    for row in ws[cell_range]:
        for cell in row:
            cell.border = BORDER

def _merge_and_write(ws, cell_range, value, font=FONT_NORMAL, align=ALIGN_CENTER):
    ws.merge_cells(cell_range)
    first = ws[cell_range.split(":")[0]]
    first.value = value
    first.font = font
    first.alignment = align
    _set_borders(ws, cell_range)

def _fmt_num(v):
    """Форматирование попыток: -1.0 превращается в 'X', 0.0 в прочерк."""
    if v is None or v == "" or v == 0.0:
        return DASH
    if v == -1.0:
        return "X"
    try:
        return f"{float(v):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        return str(v)

def _fmt_wind(w):
    if w is None or w == "" or w == 0.0:
        return DASH
    try:
        val = float(w)
    except (TypeError, ValueError):
        return str(w)
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f}".replace(".", ",")

def export_technical_protocol(athletes, event_info):
    wb = Workbook()
    ws = wb.active
    ws.title = event_info.get("discipline", "Протокол")

    widths = {
        "A": 6, "B": 6, "C": 26, "D": 12, "E": 8, "F": 14, "G": 22,
        "H": 10, "I": 7, "J": 7, "K": 7, "L": 7, "M": 7, "N": 7,
        "O": 7, "P": 7, "Q": 7, "R": 7, "S": 7, "T": 7, "U": 7,
        "V": 12, "W": 4, "X": 10, "Y": 22, "Z": 10,
    }
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    _merge_and_write(ws, "A1:Z1", "АДМИНИСТРАЦИЯ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A2:Z2", "УПРАВЛЕНИЕ КУЛЬТУРЫ, МОЛОДЕЖИ И СПОРТА АДМИНИСТРАЦИИ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A3:Z3", "ФЕДЕРАЦИЯ ЛЕГКОЙ АТЛЕТИКИ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A4:Z4", "СПОРТИВНАЯ ШКОЛА ОЛИМПИЙСКОГО РЕЗЕРВА ПО ЛЕГКОЙ АТЛЕТИКЕ ГОРОДА АБАКАНА", FONT_TITLE)
    _merge_and_write(ws, "A5:Z5", event_info.get("venue", ""), FONT_NORMAL, ALIGN_LEFT)
    _merge_and_write(ws, "A6:Z6", event_info.get("title", ""), FONT_NORMAL, ALIGN_LEFT)

    rm = event_info.get("rm", ("", ""))
    re_ = event_info.get("re", ("", ""))
    rr = event_info.get("rr", ("", ""))

    ws["B8"] = "РМ"; ws["C8"] = f"{rm[0]} {rm[1]}"
    ws["B9"] = "РЕ"; ws["C9"] = f"{re_[0]} {re_[1]}"
    ws["B10"] = "РР"; ws["C10"] = f"{rr[0]} {rr[1]}"
    for r in (8, 9, 10):
        ws[f"B{r}"].font = FONT_SMALL
        ws[f"C{r}"].font = FONT_SMALL
        ws[f"C{r}"].alignment = ALIGN_LEFT

    ws["D8"] = "СТАРТОВЫЙ ПРОТОКОЛ"; ws["D8"].font = FONT_TITLE
    ws["D9"] = event_info.get("gender", "МУЖЧИНЫ"); ws["D9"].font = FONT_TITLE
    ws["D10"] = event_info.get("discipline", "Технический вид"); ws["D10"].font = FONT_TITLE

    _merge_and_write(ws, "S7:U7", "Название этапа", FONT_SMALL)
    _merge_and_write(ws, "V7:X7", event_info.get("stage", "финальные соревнования"), FONT_SMALL)
    _merge_and_write(ws, "S8:U8", "Дата проведения", FONT_SMALL)
    _merge_and_write(ws, "V8:X8", str(event_info.get("date", "")), FONT_SMALL)
    _merge_and_write(ws, "S9:U9", "Время", FONT_SMALL)
    _merge_and_write(ws, "V9:X9", str(event_info.get("time", "")), FONT_SMALL)

    # --- РАСЧЕТ МЕСТ ДО СОРТИРОВКИ ---
    results = [a.get("result") for a in athletes]
    places = calculate_place(results)
    
    # Сохраняем посчитанное место внутрь данных каждого спортсмена
    for idx, a in enumerate(athletes):
        a["place"] = places[idx]
    
    discipline_name = event_info.get("discipline", "длина").lower()
    gender_str = event_info.get("gender", "МУЖЧИНЫ").lower()
    gender_key = "ж" if "жен" in gender_str else "м"

    headers = [
        "№ уч.", "№п/п", "Фамилия Имя", "Дата рождения", "Заявл. разряд",
        "Регион, МО", "Ведомственная принадлежность Организация", "Рез-т квал.",
        "1", "Ветер", "2", "Ветер", "3", "Ветер", "Ж",
        "4", "Ветер", "5", "Ветер", "6", "Ветер",
        "Результат", "", "Выполн. разряд", "тренеры", "Очки и Бонус",
    ]
    for idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=12, column=idx, value=h)
        cell.font = FONT_SMALL
        cell.alignment = ALIGN_CENTER
        cell.border = BORDER

    # --- СОРТИРОВКА ДЛЯ ВЫВОДА ---
    athletes.sort(key=lambda x: x.get("result") if x.get("result") is not None else -1, reverse=True)

    start_row = 13
    for i, a in enumerate(athletes):
        r = start_row + i
        attempts = (a.get("attempts") or []) + [None] * (6 - len(a.get("attempts") or []))
        winds = (a.get("winds") or []) + [None] * (6 - len(a.get("winds") or []))
        result = a.get("result")
        
        # Считаем разряд с учетом пола
        rank_done = calculate_rank(result, discipline_name, gender_key)
        
        # Берем место, которое посчитали ранее, а не индекс строки
        place = a.get("place")
        points = calculate_points(place)

        # Добавляем звездочку к результату, если это рекорд
        result_str = _fmt_num(result)
        if a.get("is_record"):
            result_str += "*"

        row_values = [
            a.get("num", ""), a.get("order", ""), a.get("name", ""),
            str(a.get("birth", "")), a.get("rank", ""), a.get("region", ""),
            a.get("org", ""), "", 
            _fmt_num(attempts[0]), _fmt_wind(winds[0]),
            _fmt_num(attempts[1]), _fmt_wind(winds[1]),
            _fmt_num(attempts[2]), _fmt_wind(winds[2]),
            "", 
            _fmt_num(attempts[3]), _fmt_wind(winds[3]),
            _fmt_num(attempts[4]), _fmt_wind(winds[4]),
            _fmt_num(attempts[5]), _fmt_wind(winds[5]),
            result_str, "",
            rank_done, a.get("coaches", ""), points,
        ]
        for col, val in enumerate(row_values, start=1):
            cell = ws.cell(row=r, column=col, value=val)
            cell.font = FONT_NORMAL
            cell.alignment = ALIGN_CENTER if col not in (3, 7, 25) else ALIGN_LEFT
            cell.border = BORDER

    last_data_row = start_row + len(athletes) - 1 if athletes else start_row

    footer = last_data_row + 2
    ws.cell(row=footer, column=4, value="Рефери ___ ( ________________________________________________________ )").font = FONT_NORMAL
    ws.cell(row=footer + 1, column=4, value="Ст. судья ___ ( _____________________________________________________ )").font = FONT_NORMAL
    ws.cell(row=footer + 2, column=4, value="Секретарь __( _______________________________________________________ )").font = FONT_NORMAL

    ws.cell(row=footer + 4, column=3, value="Главный судья").font = FONT_NORMAL
    ws.cell(row=footer + 4, column=5, value=event_info.get("chief_judge", "Ромащенко А.А., СС 1К, Абакан")).font = FONT_NORMAL
    ws.cell(row=footer + 6, column=3, value="Главный секретарь").font = FONT_NORMAL
    ws.cell(row=footer + 6, column=5, value=event_info.get("chief_secretary", "Скоринова М.А., ССВК, Абакан")).font = FONT_NORMAL
    ws.cell(row=footer + 8, column=3, value=f"Дата формирования протокола: {date.today().strftime('%d.%m.%Y')}").font = FONT_SMALL
    ws.cell(row=footer + 8, column=12, value=f"Количество участников: {len(athletes)}").font = FONT_SMALL

    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    return wb
