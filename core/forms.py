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
        
        # 1. Читаем заголовки видов из 2-й строки (начиная с 13-й колонки, т.е. M)
        event_columns = {}
        for idx, cell in enumerate(sheet[2]):
            if idx >= 12 and cell.value: # Берем все колонки после L (12)
                event_columns[idx] = str(cell.value).strip()

        # 2. Проходим по спортсменам (с 3-й строки)
        for row in sheet.iter_rows(min_row=3, values_only=True):
            if not row[3]: # Если нет ФИО
                continue
                
            full_name = str(row[3]).strip()
            birth_date_val = row[4]
            
            birth_date = None
            if isinstance(birth_date_val, datetime):
                birth_date = birth_date_val.date()
                
            rank = str(row[5]) if row[5] else ""
            region = str(row[6]) if row[6] else ""
            organization = str(row[7]) if row[7] else ""
            coach = str(row[8]) if row[8] else ""
            
            gender_raw = str(row[10]).strip().upper() if row[10] else "М"
            gender = "Ж" if gender_raw in ["Ж", "ЖЕН"] else "М"

            # Создаем спортсмена (get_or_create защитит от дублей)
            athlete, created = Athlete.objects.get_or_create(
                competition=comp,
                full_name=full_name,
                defaults={
                    'birth_date': birth_date,
                    'rank': rank,
                    'region': region,
                    'organization': organization,
                    'coach': coach
                }
            )
            
            # Определяем возрастную категорию
            category = "2008 и ст."
            if birth_date:
                year = birth_date.year
                if year in [2009, 2010]: category = "2009-2010"
                elif year in [2011, 2012]: category = "2011-2012"

            # 3. Ищем заполненные ячейки с результатами
            for col_idx, event_name in event_columns.items():
                if col_idx < len(row) and row[col_idx]:
                    declared_val = str(row[col_idx]).strip()
                    
                    # Определяем, беговой это вид или технический
                    is_run = any(x in event_name.lower() for x in ['бег', 'метр', '100', '200', '400', '800', '1500', '3000', 'с/б'])
                    
                    # Ищем вид в базе (или создаем)
                    event_obj, e_created = Event.objects.get_or_create(
                        competition=comp,
                        name=event_name,
                        gender=gender,
                        category=category,
                        defaults={
                            'is_technical': not is_run,
                            'is_running': is_run
                        }
                    )
                    
                    # Создаем результат с заявленным значением
                    Result.objects.update_or_create(
                        event=event_obj,
                        athlete=athlete,
                        defaults={'declared_result': declared_val}
                    )
            
            created_count += 1
            
        return created_count
