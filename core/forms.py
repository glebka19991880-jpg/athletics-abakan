from django import forms
import openpyxl
from datetime import datetime
from .models import Athlete, Competition

class ImportExcelForm(forms.Form):
    competition = forms.ModelChoiceField(queryset=Competition.objects.all(), label="Соревнование")
    excel_file = forms.FileField(label="Файл Excel")

    def save(self):
        comp = self.cleaned_data['competition']
        file = self.cleaned_data['excel_file']
        
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb['УЧАСТНИКИ']  # Имя листа из вашего файла
        
        created_count = 0
        # Данные начинаются с 3-й строки (2-я - заголовки)
        for row in sheet.iter_rows(min_row=3, values_only=True):
            if not row[3]: # Если нет ФИО (столбец D, индекс 3)
                continue
                
            full_name = row[3].strip()
            birth_date_val = row[4]
            
            # Обработка даты рождения
            birth_date = None
            if isinstance(birth_date_val, datetime):
                birth_date = birth_date_val.date()
                
            rank = str(row[5]) if row[5] else ""
            region = str(row[6]) if row[6] else ""
            organization = str(row[7]) if row[7] else ""
            coach = str(row[8]) if row[8] else ""

            Athlete.objects.create(
                competition=comp,
                full_name=full_name,
                birth_date=birth_date,
                rank=rank,
                region=region,
                organization=organization,
                coach=coach
            )
            created_count += 1
            
        return created_count
