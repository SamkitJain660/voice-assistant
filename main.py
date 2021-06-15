from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import playsound
import speech_recognition as sr
import pyttsx3
import pytz
import subprocess
import pywhatkit
import sys
import webbrowser

songPhrases = ['play']
notePhrases = ['Make a note ', 'note down ', 'type ']
searchStrings = ['search ', 'whats ', 'google ']
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november',
          'december']
DAYS = ['monday', 'tuesday', 'friday', 'saturday', 'sunday']
DAY_EXTENSIONS = ['rd', 'th', 'st', 'nd']


def speak(text):
    hazel = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-GB_HAZEL_11.0"
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', hazel)
    engine.setProperty('rate', 145)
    for voice in voices:
        print(voice.name)
        print(voice)
    engine.say(text)
    engine.runAndWait()


speak('There is no one who loves pain itself, who seeks after it and wants to have it, simply because it is pain')


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ''

        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
            print("Exception: " + str(e))
    return said


def authenticate_google():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def get_events(day, service):
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end = end.astimezone(utc)
    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end.isoformat(),
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f'You have {len(events)} events on this day.')

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split('T')[1].split("-")[0])

            if int(start_time.split(":")[0]) < 12:
                start_time = start_time + " AM"
            else:
                start_time = str(int(start_time.split(":")[0]) - 12)
                start_time = start_time + " PM"

        speak(event['summary'] + ' at ' + start_time)


def get_date(text):
    text = text.lower()
    today = datetime.date.today()

    if text.count("today") > 0:
        return today

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENSIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass
    if month < today.month and month != -1:
        year = year + 1

    if month == -1 and day != -1:
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week

        if dif < 0:
            dif += 7
            if text.count("next") >= 1:
                dif += 7

        return today + datetime.timedelta(dif)

    if day != -1:
        return datetime.date(month=month, day=day, year=year)


def note(text):
    speak('Making a note')
    date = datetime.datetime.now()
    file_name = str(date).replace(":", '-') + '-note.txt'
    with open(file_name, 'w') as f:
        f.write(text)

    subprocess.Popen(['notepad.exe', file_name])


def search_google(text):
    try:
        speak(f'searching {text} on google')
        time.sleep(1)
        speak('showing the results on your screen now')
        pywhatkit.search(text)
    except:
        speak('something went wrong. Please try again later many a network issue')


def play_song(text):
    speak(f'Playing {text} on youtube')
    pywhatkit.playonyt(text)


service = authenticate_google()
print('google authenticated.')

text = get_audio()

calStrings = ['what do I have', 'do I have plans on', 'am I busy', 'is there anything']
for phrase in calStrings:
    if phrase in text:
        date = get_date(text)
        if date:
            get_events(date, service)
        else:
            speak('Please try again')

for phrase in searchStrings:
    if phrase in text.lower():
        phraseLen = len(phrase)
        searchPhrase = text[phraseLen:]
        search_google(searchPhrase)

for phrase in notePhrases:
    if phrase in text.lower():
        noteLen = len(phrase)
        noteContent = text[noteLen:]
        note(noteContent)

for phrase in songPhrases:
    if phrase in text.lower():
        songLen = len(phrase)
        songName = text[songLen:]
        play_song(songName)
