import os
import base64
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from icalendar import Calendar, Event
import dateparser
import io
import re

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

NUMBER_WORDS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'half': 0.5
}
EVENT_KEYWORDS = [
    'meeting', 'appointment', 'lunch', 'dinner', 'workout', 'call', 'session', 'class', 'conference',
    'doctor', 'business', 'study', 'exam', 'party', 'birthday', 'anniversary', 'interview', 'presentation',
    'review', 'discussion', 'seminar', 'webinar', 'training', 'visit', 'picnic', 'trip', 'travel', 'holiday',
    'breakfast', 'brunch', 'supper', 'gathering', 'ceremony', 'event', 'lecture', 'practice', 'game', 'match',
    'meditation', 'yoga', 'exercise', 'break', 'rest', 'walk', 'run', 'task', 'work', 'project', 
    'therapy', 'massage', 'nap', 'sleep', 'reading', 'book', 'movie', 'show', 'shopping', 'cleanup',
    'cooking', 'cleaning', 'laundry', 'maintenance', 'repair', 'check', 'reminder', 'followup'
]
EVENT_KEYWORDS_PATTERN = '|'.join(EVENT_KEYWORDS)
# Split on 'and', 'also', 'then' only if followed by an event keyword
SPLIT_PATTERN = re.compile(rf'\b(?:and|also|then)\b(?=\s+(?:a\s+)?(?:{EVENT_KEYWORDS_PATTERN})\b)', re.IGNORECASE)

def parse_duration(text):
    # Support hours, days, weeks, and ranges
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hr|h)s?', text, re.IGNORECASE)
    if match:
        return float(match.group(1)), 'hours'
    match = re.search(r'((?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|half))\s*(?:hour|hr|h)s?', text, re.IGNORECASE)
    if match:
        word = match.group(1).lower()
        return float(NUMBER_WORDS.get(word, 1)), 'hours'
    match = re.search(r'(\d+)\s*(?:minute|min|m)s?', text, re.IGNORECASE)
    if match:
        return float(match.group(1)) / 60.0, 'hours'
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:day|days)', text, re.IGNORECASE)
    if match:
        return float(match.group(1)), 'days'
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:week|weeks)', text, re.IGNORECASE)
    if match:
        return float(match.group(1)), 'weeks'
    # Range: from X to Y
    if re.search(r'from .+ to .+', text, re.IGNORECASE):
        return None, 'range'
    if re.search(r'half\s+(?:an\s+)?hour', text, re.IGNORECASE):
        return 0.5, 'hours'
    if re.search(r'quarter\s+(?:of\s+an\s+)?hour', text, re.IGNORECASE):
        return 0.25, 'hours'
    return 1.0, 'hours'

def extract_event_name(text):
    # Remove common time/date/duration phrases
    clean_text = re.sub(r'\b(?:at|on|by|around|for|from)\s+[^.,\n]+', '', text, flags=re.IGNORECASE)
    clean_text = re.sub(r'\b(tomorrow|today|next week|this week|am|pm|a\.m\.|p\.m\.)\b', '', clean_text, flags=re.IGNORECASE)
    # Look for a phrase with a keyword in it
    for keyword in EVENT_KEYWORDS:
        match = re.search(rf'([\w\s]+)?\b{keyword}\b([\w\s]*)?', clean_text, re.IGNORECASE)
        if match:
            phrase = match.group(0).strip()
            # Remove trailing 'for', 'at', 'on', etc. and anything after
            phrase = re.split(r'\b(for|at|on|by|around|from)\b', phrase)[0].strip()
            return phrase[0].upper() + phrase[1:]
    return ' '.join(text.split()[:4]).capitalize() or 'Event'

def extract_time(text):
    match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)', text, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3).lower()
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        try:
            return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            pass
    match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', text, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3).lower()
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        try:
            return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            pass
    match = re.search(r'(?:at\s+)?(\d{1,2}):(\d{2})\b', text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        try:
            return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            pass
    time_expressions = re.findall(r'(?:at|by|around)\s+([^,.\n]+?)(?:\s+(?:for|tomorrow|today|on|$))', text, re.IGNORECASE)
    for expr in time_expressions:
        try:
            parsed = dateparser.parse(expr)
            if parsed:
                return parsed
        except:
            continue
    return None

def extract_date_range(text):
    # Look for 'from X to Y' or 'between X and Y'
    match = re.search(r'(?:from|between)\s+([^,\n]+?)\s+(?:to|and)\s+([^,\n]+)', text, re.IGNORECASE)
    if match:
        start_str, end_str = match.group(1), match.group(2)
        # Always use current year if not specified
        now = datetime.now()
        start_date = dateparser.parse(start_str, settings={'PREFER_DATES_FROM': 'future'})
        end_date = dateparser.parse(end_str, settings={'PREFER_DATES_FROM': 'future'})
        if start_date and end_date:
            # If year is missing, set to this year (or next if already passed)
            if start_date.year == 1900:
                start_date = start_date.replace(year=now.year)
                if start_date < now:
                    start_date = start_date.replace(year=now.year + 1)
            if end_date.year == 1900:
                end_date = end_date.replace(year=now.year)
                if end_date < start_date:
                    end_date = end_date.replace(year=now.year + 1)
            return start_date, end_date
    return None, None

def extract_date(text):
    date_patterns = [
        r'\b(tomorrow|today)\b',
        r'\b(next|this)\s+(\w+day)\b',
        r'\b(\w+day)\s+(next|this)\s+week\b',
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b',
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b',
        r'\b\d{1,2}-\d{1,2}(?:-\d{2,4})?\b'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                now = datetime.now()
                dt = dateparser.parse(match.group(0), settings={'PREFER_DATES_FROM': 'future'})
                if dt:
                    # If year is missing, set to this year (or next if already passed)
                    if dt.year == 1900:
                        dt = dt.replace(year=now.year)
                        if dt < now:
                            dt = dt.replace(year=now.year + 1)
                    return dt
            except:
                continue
    return None

def parse_text_to_events(text):
    # First split on sentence boundaries (periods, exclamation marks, question marks, newlines)
    sentence_splits = re.split(r'[.!?\n]+', text)
    event_texts = []
    for sentence in sentence_splits:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Only split if there are multiple real events
        if re.search(r'\b(and|also|then)\b', sentence, re.IGNORECASE):
            parts = []
            last = 0
            for m in SPLIT_PATTERN.finditer(sentence):
                start = m.start()
                if last < start:
                    parts.append(sentence[last:start].strip())
                last = start
            parts.append(sentence[last:].strip())
            # Merge non-keyword parts with previous event
            merged = []
            for part in parts:
                if any(kw in part.lower() for kw in EVENT_KEYWORDS):
                    merged.append(part)
                elif merged:
                    merged[-1] += ' ' + part
            sub_events = merged
        else:
            sub_events = [sentence]
        # FINAL FILTER: Only keep if the fragment contains an event keyword
        for e in sub_events:
            cleaned = e.strip(' .,!').lower()
            if cleaned and len(cleaned) > 4 and any(kw in cleaned for kw in EVENT_KEYWORDS):
                event_texts.append(e.strip(' .,!'))
    # Remove duplicates (case-insensitive)
    unique_events = []
    for e in event_texts:
        if e.lower() not in [ev.lower() for ev in unique_events]:
            unique_events.append(e)
    events = []
    calendar = Calendar()
    prev_end_time = None
    prev_date = None
    now = datetime.now()
    for idx, event_text in enumerate(unique_events):
        summary = extract_event_name(event_text)
        # Check for date range first
        start_range, end_range = extract_date_range(event_text)
        if start_range and end_range:
            start_datetime = start_range
            end_datetime = end_range
            # Try to extract time for start (if any)
            parsed_time = extract_time(event_text)
            if parsed_time:
                start_datetime = start_datetime.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
            else:
                start_datetime = start_datetime.replace(hour=10, minute=0, second=0, microsecond=0)
            # End time is end of day
            end_datetime = end_datetime.replace(hour=23, minute=59, second=0, microsecond=0)
        else:
            parsed_date = extract_date(event_text)
            parsed_time = extract_time(event_text)
            duration, duration_type = parse_duration(event_text)
            if not parsed_date:
                parsed_date = prev_date if prev_date else now
            prev_date = parsed_date
            if not parsed_time and prev_end_time:
                start_datetime = prev_end_time
            else:
                if not parsed_time:
                    current_hour = now.hour
                    if current_hour < 12:
                        default_hour = 10
                    elif current_hour < 17:
                        default_hour = 14
                    else:
                        default_hour = 19
                    parsed_time = now.replace(hour=default_hour, minute=0, second=0, microsecond=0)
                start_datetime = parsed_date.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute,
                    second=0,
                    microsecond=0
                )
                # If the event is for today but the time is in the past, schedule for tomorrow
                if not extract_date(event_text) and start_datetime < now:
                    start_datetime = start_datetime + timedelta(days=1)
            # If the event is still in the past, return an error
            if start_datetime < now:
                return {
                    'success': False,
                    'error': 'The specified time is in the past. Please provide a future time or date.'
                }
            # Calculate end_datetime based on duration type
            if duration_type == 'hours':
                end_datetime = start_datetime + timedelta(hours=duration if duration is not None else 1)
            elif duration_type == 'days':
                end_datetime = start_datetime + timedelta(days=duration if duration is not None else 1)
            elif duration_type == 'weeks':
                end_datetime = start_datetime + timedelta(weeks=duration if duration is not None else 1)
            else:
                end_datetime = start_datetime + timedelta(hours=1)
        prev_end_time = end_datetime
        event = Event()
        event.add('summary', summary)
        event.add('dtstart', start_datetime)
        event.add('dtend', end_datetime)
        calendar.add_component(event)
        events.append({
            'summary': summary,
            'start': start_datetime.isoformat(),
            'end': end_datetime.isoformat()
        })
    ics_file = base64.b64encode(calendar.to_ical()).decode('utf-8')
    return {
        'success': True,
        'events': events,
        'ics_file': ics_file,
        'single_event': len(events) == 1
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': 'No text provided'})
        transcript = data['text']
        if not transcript.strip():
            return jsonify({'success': False, 'error': 'No speech detected'})
        result = parse_text_to_events(transcript)
        result['transcript'] = transcript
        return jsonify(result)
    except Exception as e:
        log.error(f"Error in transcribe endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/calendar.ics')
def download_calendar():
    try:
        data = request.args.get('data')
        if not data:
            return jsonify({'success': False, 'error': 'No calendar data provided'})
        ics_content = base64.b64decode(data)
        file_obj = io.BytesIO(ics_content)
        file_obj.seek(0)
        return send_file(
            file_obj,
            mimetype='text/calendar',
            as_attachment=True,
            download_name='calendar.ics'
        )
    except Exception as e:
        log.error(f"Error in download endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Starting VoxCal - Voice to Calendar Application")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 
