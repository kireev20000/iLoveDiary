import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    date: datetime = datetime.datetime.now()
    return {'year': date.year}
