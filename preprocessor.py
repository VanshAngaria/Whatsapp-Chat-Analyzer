import re
import pandas as pd

def preprocess(data):
    # Normalize unicode whitespace characters (narrow non-breaking space, non-breaking space) and dash variants
    data = data.replace('\u202f', ' ').replace('\xa0', ' ')
    data = data.replace('\u2013', '-').replace('\u2014', '-')

    # RegEx Patterns to split messages and find date/time prefixes
    # Pattern 1: Standard non-bracketed format (Android/web: e.g. 18/10/24, 1:41 pm - or 18/10/2024, 13:41 -)
    pattern1 = r'\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?(?:\s?[aApP]\.?[mM]\.?)?\s-\s'
    # Pattern 2: Bracketed iOS format (e.g. [18/10/24, 1:41:05 PM] or [18/10/2024, 13:41:05])
    pattern2 = r'\[\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?(?:\s?[aApP]\.?[mM]\.?)?\]\s?'

    if len(re.findall(pattern1, data)) > 0:
        pattern = pattern1
    elif len(re.findall(pattern2, data)) > 0:
        pattern = pattern2
    else:
        pattern = r'\[?\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?(?:\s?[aApP]\.?[mM]\.?)?\]?\s?-\s?'

    messages = re.split(pattern, data)[1:]
    dates = re.findall(pattern, data)

    if not dates or not messages:
        return pd.DataFrame(columns=[
            'date', 'user', 'message', 'only_date', 'year', 'month_num',
            'month', 'day', 'day_name', 'hour', 'minute', 'period'
        ])

    df = pd.DataFrame({'user_message': messages, 'message_date': dates})

    cleaned_dates = (
        df['message_date']
        .str.strip()
        .str.replace(r'^\[|\]$', '', regex=True)
        .str.replace(r'\s*-\s*$', '', regex=True)
        .str.strip()
    )

    try:
        parsed_dates = pd.to_datetime(cleaned_dates, format='mixed', dayfirst=True)
    except Exception:
        parsed_dates = pd.to_datetime(cleaned_dates, errors='coerce', dayfirst=True)

    df['date'] = parsed_dates

    users = []
    message_text = []
    for message in df['user_message']:
        entry = re.split(r'([\w\W]+?):\s', message, maxsplit=1)
        if len(entry) > 1:  # user name present
            users.append(entry[1])
            message_text.append(entry[2])
        else:
            users.append('group_notification')
            message_text.append(entry[0])

    df['user'] = users
    df['message'] = message_text
    df.drop(columns=['user_message'], inplace=True)

    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    period = []
    for hour in df['hour']:
        if pd.isna(hour):
            period.append("00-01")
        elif hour == 23:
            period.append("23-00")
        elif hour == 0:
            period.append("00-01")
        else:
            period.append(f"{int(hour):02d}-{(int(hour)+1):02d}")

    df['period'] = period
    return df