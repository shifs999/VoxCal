# *`VoxCal`* : Speech-driven calendar management web app

*`VoxCal`* is a speech driven web application that lets users speak naturally to create calendar events. It features live speech-to-text, natural language event parsing (including durations and sequential timing), and a nice, accessible UI. Users can add single events <ins>*directly*</ins> to Google Calendar or download multiple events as a `.ics` file for import into any calendar app. Users can also scan the QR code for accessing the service through their smartphones.

[Deployed link](https://voxcal.onrender.com/) :-   Try it out! (The project is currently in testing phase and still needs some improvements to handle some edge cases, I'll be working on better model integration and core logic for better performance)

---

## Features

- **Live Voice Recognition**: Speak your events naturally using your browser's microphone.
- **Smart Event Parsing**: Extracts event names, times, dates, and durations from natural language. Implemented from scratch for better self understanding of core concepts of parsing.
- **Google Calendar Integration**: Add single events directly to your Google Calendar.
- **ICS File Download**: Download multiple events as a `.ics` file for easy import.
- **Mobile Friendly**: Responsive design and QR code for easy mobile access.
- **No API Key Required**: All speech recognition is handled in-browser for privacy and zero cost but then efficient STT conversion is the part where we have compromised at in this case.
- **Tech Stack**:  Python 3, Flask, Flask-CORS, icalendar, dateparser, HTML5, CSS3, JavaScript (Web Speech API)

---

## Dependencies

- [Flask](https://flask.palletsprojects.com/)
- [dateparser](https://dateparser.readthedocs.io/)
- [icalendar](https://icalendar.readthedocs.io/)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [QR Code API](https://goqr.me/api/)

Note :- Please speak in a clear and concise manner in a continuous flow for accurate voice capture and wait for a few seconds of processing. For proper functioning, please mention maximum of 2 events in a single speech. Here, I am using browser-based speech recognition via Web Speech API. In future, I might make use of OpenAI `Whisper` for highly accurate results. For using OpenAI `Whisper` model please create an OpenAI API key and make required changes in app.py

---

## Fixed some edge cases in recent update

### 1. **Date Parsing**
- **Explicit Dates Without Year:**  
- **Explicit Dates With Year:**  
- **Ambiguous Dates:**  
- **Relative Dates:**  

### 2. **Time Parsing**
- **Default Time Assignment:**  
  - If no time is specified, assigns a default time based on the current time of day (morning, afternoon, evening).

### 3. **Duration and Range Parsing**
- **Single Duration (Hours/Minutes):**  
  - Input: `"for 2 hours"`, `"for 30 minutes"`
  - **Handled:** Event duration is set accordingly.
- **Multi-Day Events:**  
  - Input: `"for 3 days"`, `"for 1 week"`
  - **Handled:** Event end time is set to the correct number of days/weeks after the start.
- **Date Ranges:**  
  - Input: `"from 1st July to 7th July"`, `"between 10th August and 15th August"`
  - **Handled:** Event starts at the beginning of the first date and ends at the end of the last date (23:59).
- **Fallback Duration:**  
  - If no duration or range is specified, defaults to a 1-hour event.

### 4. **Past Dates and Times**
- **Prevents Scheduling in the Past:**  
  - If the parsed date/time is in the past, the system returns an error and asks for a future date/time.

### 5. **Robustness**
- **Handles Both Numeric and Word Durations:**  
  - Input: `"for two hours"`, `"for half an hour"`
    
### Example Inputs for Testing

- `"study session at 8:00 p.m. on 12th July"`
- `"business meeting tomorrow at 10am"`
- `"family event next Monday"`
- `"group discussion at 10am and lunch at 1pm"`
- `"conference from 5th August 2025 to 10th August 2025"`

---

## Installation & Usage

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/shifs999/VoxCal.git
cd VoxCal
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application Locally

#### On Windows:
```bash
python app.py
```

#### On macOS/Linux:
```bash
python3 app.py
```

- The app will be available at: localhost:5000

---

## Usage Instructions

1. **Click the microphone button** to start recording.
2. **Speak naturally** about your events as told in instructions, e.g.:
   - "Schedule a meeting tomorrow at 2pm for one hour"
   - "Doctor appointment on July 2nd at 10am"
   - "Lunch with family next Friday at noon for half an hour"
3. **Click the microphone again** to stop recording.
4. **Review your events** in the preview.
5. **Choose your action:**
   - For single events: Click "Add to Google Calendar"
   - For multiple events: Click "Download .ics File"
6. **Scan the QR code** on the homepage to open VoxCal on your mobile device.

---

## API Endpoints

- `GET /`  Main application page
- `POST /transcribe`  Process recognized text and generate calendar events
- `GET /download/calendar.ics`  Download generated ICS file

---

## Supported Platforms

| Platform         | Speech Recognition | Notes                        |
|------------------|-------------------|------------------------------|
| Desktop Chrome   | Y               | Full support                 |
| Desktop Edge     | Y                | Full support                 |
| Desktop Firefox  | N                | Not supported                |
| Android Chrome   | Y (HTTPS only)   | Use deployed HTTPS URL       |
| iOS Safari/Chrome| N                | Not supported by Apple       |

---

## Troubleshooting

- **Microphone not working?**
  - Allow microphone access in your browser.
  - Use Chrome for best results.
  - On mobile, use the HTTPS Render.com URL.

- **Speech recognition not supported?**
  - Some browsers (e.g., iOS Safari, Firefox) do not support the Web Speech API.

- **Events not parsing correctly?**
  - Speak clearly and specify times/dates.
  - Use natural language like "tomorrow at 2pm" or "next Friday at noon".

---

## Contributions 

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## Contact

For any queries or collaborations, feel free to reach me out at **saizen777999@gmail.com**
