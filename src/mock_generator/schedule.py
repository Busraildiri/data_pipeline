from datetime import timedelta


def missing_business_dates(last_generated_date, through_date):
    """Son üretilen tarihten hedef tarihe kadar eksik takvim günlerini döndürür."""
    if last_generated_date is None:
        return [through_date]

    dates = []
    current_date = last_generated_date + timedelta(days=1)
    while current_date <= through_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    return dates
