import calendar
import datetime

SPANISH_MONTHS = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}

MONTH_NUMBER_BY_ABBR = {abbr: number for number, abbr in SPANISH_MONTHS.items()}


def period_sort_key(period):
    """Convierte un periodo tipo 'jun-26' en una tupla (año, mes) para poder
    ordenarlo cronologicamente. Periodos no reconocidos quedan al final."""
    if not period:
        return (0, 0)
    parts = str(period).strip().lower().split("-")
    if len(parts) != 2:
        return (0, 0)
    month_abbr, year_part = parts
    month = MONTH_NUMBER_BY_ABBR.get(month_abbr)
    if month is None:
        return (0, 0)
    try:
        year = int(year_part)
    except ValueError:
        return (0, 0)
    return (year, month)


def period_for_date(date_obj):
    """Retorna el periodo (ej: 'ago-26') correspondiente a una fecha."""
    return f"{SPANISH_MONTHS[date_obj.month]}-{str(date_obj.year)[2:]}"


def get_week_bounds(date_obj):
    """Dada una fecha, calcula a que 'semana' (1-5) del mes pertenece segun
    la regla de negocio: las semanas son bloques lunes-viernes, contados
    desde el primer lunes del mes. Los dias sueltos antes del primer lunes
    (si el mes no empieza en lunes) no pertenecen a ninguna semana.

    Retorna (period, week_number, week_start, week_end) o None si la fecha
    cae antes del primer lunes del mes (dias sueltos sin semana asignada).
    """
    year, month = date_obj.year, date_obj.month
    first_of_month = datetime.date(year, month, 1)
    days_until_monday = (0 - first_of_month.weekday()) % 7
    first_monday = first_of_month + datetime.timedelta(days=days_until_monday)

    if date_obj < first_monday:
        return None

    days_since_first_monday = (date_obj - first_monday).days
    week_number = days_since_first_monday // 7 + 1
    if week_number > 5:
        return None

    week_start = first_monday + datetime.timedelta(weeks=week_number - 1)
    week_end = week_start + datetime.timedelta(days=4)

    last_day_of_month = datetime.date(year, month, calendar.monthrange(year, month)[1])
    if week_start > last_day_of_month:
        return None
    if week_end > last_day_of_month:
        week_end = last_day_of_month

    period = period_for_date(date_obj)
    return period, week_number, week_start, week_end
