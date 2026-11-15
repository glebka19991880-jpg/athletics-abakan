from django import forms
import openpyxl
from datetime import datetime
from .models import Athlete, Competition, Event, Result

class ImportExcelForm(forms.Form):
    competition = forms.ModelChoiceField(queryset=Competition.objects.all(), label="Соревнование")
    excel_file = forms.FileField(label="Файл Excel")

    def save(self):
        comp = self.cleaned_data['competition']
        file = self.cleaned_data['excel_file']
        
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb['УЧАСТНИКИ']
        
        created_count = 0
        
        # Карта столбцов: индекс колонки (начиная с 0) -> Название вида
        # M=12 (100м), N=13 (200м), O=14 (400м), P=15 (800м), Q=16 (1500м), R=17 (3000м)
        # S=18 (110сб), T=19 (высота), U=20 (длина), V=21 (тройной), W=22 (ядро)
        events_map = {
            12: 'Бег 100 м', 13: 'Бег 200 м', 14: 'Бег 400 м', 15: 'Бег 800 м',
            16: 'Бег 1500 м', 17: 'Бег 3000 м', 18: 'Бег 110 с/б',
            19: 'Прыжок в высоту', 20: 'Прыжок в длину', 21: 'Тройной прыжок', 22: 'Толкание ядра'
        }

        # Данные начинаются с 3-й строки (2-я - заголовки)
        for row in sheet.iter_rows(min_row=3, values_only=True):
            if not row[3]: # Если нет ФИО (столбец D, индекс 3)
                continue
                
            full_name = str(row[3]).strip()
            birth_date_val = row[4]
            
            # Обработка даты рождения
            birth_date = None
            if isinstance(birth_date_val, datetime):
                birth_date = birth_date_val.date()
                
            rank = str(row[5]) if row[5] else ""
            region = str(row[6]) if row[6] else ""
            organization = str(row[7]) if row[7] else ""
            coach = str(row[8]) if row[8] else ""
            
            # Пол (в файле столбец K, индекс 10)
            gender_raw = str(row[10]).strip().upper() if row[10] else "М"
            gender = "Ж" if gender_raw in ["Ж", "ЖЕН"] else "М"

            # Создаем спортсмена
            athlete = Athlete.objects.create(
                competition=comp,
                full_name=full_name,
                birth_date=birth_date,
                rank=rank,
                region=region,
                organization=organization,
                coach=coach
            )
            
            # Определяем возрастную категорию (упрощенно по году рождения)
            category = "2008 и ст."
            if birth_date:
                year = birth_date.year
                if year in [2009, 2010]: category = "2009-2010"
                elif year in [2011, 2012]: category = "2011-2012"

            # Проходим по всем возможным видам
            for col_idx, event_name in events_map.items():
                if col_idx < len(row) and row[col_idx]:
                    declared_val = str(row[col_idx]).strip()
                    
                    # Ищем подходящий вид в базе (по названию, полу и категории)
                    event_obj = Event.objects.filter(
                        competition=comp,
                        name__icontains=event_name,
                        gender__iexact=gender,
                        category__icontains=category
                    ).first()
                    
                    # Если вида нет - создаем его
                    if not event_obj:
                        is_run = event_name.startswith('Бег')
                        event_obj = Event.objects.create(
                            competition=comp,
                            name=event_name,
                            gender=gender,
                            category=category,
                            is_technical=not is_run,
                            is_running=is_run
                        )
                    
                    # Создаем результат с заявленным значением
                    Result.objects.create(
                        event=event_obj,
                        athlete=athlete,
                        declared_result=declared_val
                    )
            
            created_count += 1
            
        return created_count
