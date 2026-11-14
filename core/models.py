from django.db import models

class Competition(models.Model):
    name = models.CharField("Название", max_length=200)
    city = models.CharField("Город", max_length=100, default="Абакан")
    start_date = models.DateField("Дата начала", null=True, blank=True)
    end_date = models.DateField("Дата окончания", null=True, blank=True)

    def __str__(self):
        return self.name

class Athlete(models.Model):
    full_name = models.CharField("ФИО", max_length=200)
    birth_date = models.DateField("Дата рождения", null=True, blank=True)
    rank = models.CharField("Разряд", max_length=20, blank=True)
    region = models.CharField("Регион", max_length=100, blank=True)
    organization = models.CharField("Организация", max_length=200, blank=True)
    coach = models.CharField("Тренер", max_length=200, blank=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="athletes", null=True, blank=True)

    def __str__(self):
        return self.full_name

class Event(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    name = models.CharField("Вид", max_length=100)
    gender = models.CharField("Пол", max_length=10)
    category = models.CharField("Возрастная группа", max_length=50)
    is_technical = models.BooleanField("Технический вид", default=False)

    def __str__(self):
        return f"{self.name} - {self.gender} ({self.category})"

class Result(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="results")
    athlete = models.ForeignKey(Athlete, on_delete=models.CASCADE)
    
    attempt_1 = models.FloatField("Попытка 1", null=True, blank=True)
    attempt_2 = models.FloatField("Попытка 2", null=True, blank=True)
    attempt_3 = models.FloatField("Попытка 3", null=True, blank=True)
    attempt_4 = models.FloatField("Попытка 4", null=True, blank=True)
    attempt_5 = models.FloatField("Попытка 5", null=True, blank=True)
    attempt_6 = models.FloatField("Попытка 6", null=True, blank=True)
    
    final_result = models.FloatField("Итоговый результат", null=True, blank=True)
    
    # УДАЛЕНО ВСЁ ЛИШНЕЕ, ЧТО НЕ СУЩЕСТВУЕТ В БАЗЕ

class ApiKey(models.Model):
    key = models.CharField(max_length=64, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="api_keys")
    is_active = models.BooleanField(default=True)
