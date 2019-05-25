import sqlite3
import datetime
from datetime import datetime, date
from datetime import time
from mycroft import MycroftSkill, intent_file_handler

# The class BufordSQLite that handles the sqlite database in an OOP manner
# Named to avoid confusion with the built-in SQLite libraries
class BufordSQLite:
    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self, path=""):
        # Use any name that you want here
        # TODO - this saves to the mycroft-core directory by default
        self.conn = sqlite3.connect(path + '/buford.db')

    # Query that returns nothing (e.g. INSERT)
    def emptyQuery(self, query):
        self.conn.execute(query)

    # Query that returns something. Accepted Values - Single (1R x 1C), Columns(1R x nC), Table (nR x nC)
    def returnQuery(self, query, return_type="Single"):
        if return_type == "Single":
            return self.conn.execute(query).fetchone()[0] # Returns a single object
        if return_type == "Columns":
            return self.conn.execute(query).fetchone() # Returns a row
        if return_type == "Table":
            return self.conn.execute(query).fetchall() # Returns a n x n table

    # Required in order to make changes to database
    def commit(self):
        self.conn.commit()

    # Closes Database Connection
    def close(self):
        self.conn.close()
        
# manually converts a Datetime to a string with format YYYY-MM-DD HH:MM:SS for SQLite purposes
def datetime_to_BufordSQLiteString(datetime_object):
    sql_friendly_string = str(datetime_object.year) + "-"
    if datetime_object.month >= 10:
        month = str(datetime_object.month)
    else:
        month = "0" + str(datetime_object.month)
    sql_friendly_string = sql_friendly_string + month + "-"
    if datetime_object.day >= 10:
        day = str(datetime_object.day)
    else:
        day = "0" + str(datetime_object.day)
    sql_friendly_string = sql_friendly_string + day + " "
    if datetime_object.hour >= 10:
        hour = str(datetime_object.hour)
    else:
        hour = "0" + str(datetime_object.hour)
    sql_friendly_string = sql_friendly_string + hour + ":"
    if datetime_object.minute >= 10:
        minute = str(datetime_object.minute)
    else:
        minute = "0" + str(datetime_object.minute)
    sql_friendly_string = sql_friendly_string + minute + ":"
    if datetime_object.second >= 10:
        second = str(datetime_object.second)
    else:
        second = "0" + str(datetime_object.second)
    sql_friendly_string = sql_friendly_string + second
    return str(sql_friendly_string)


# Converts a string with the YYYY-MM-DD HH:MM:SS format to a Datetime object
# TODO - will return error if other formats are used
def bufordSQLiteString_to_datetime(bufordSQLiteString):
    separated_datetime = bufordSQLiteString.split(' ')
    separate_date = separated_datetime[0]
    separate_time = separated_datetime[1]
    list_date = separate_date.split('-')
    list_time = separate_time.split(':')
    final_datetime = datetime(year = int(list_date[0]), month = int(list_date[1]), day = int(list_date[2]), hour = int(list_time[0]), minute = int(list_time[1]), second = int(list_time[2]))
    return final_datetime


class SleepTracker(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        dbconn = BufordSQLite(self.file_system.path)
        birth_year = self.settings.get("year", "")
        birth_month = self.settings.get("month", "")
        birth_day = self.settings.get("day", "")
        self.birthdate = datetime(year = birth_year, month = birth_month, day = birth_day)
        #LOG.debug(self.settings)

    @intent_file_handler('tracker.sleep.intent')
    def handle_tracker_sleep(self, message):
        #self.speak_dialog('tracker.sleep')
        self.speak("Year: " + str(self.birthdate.year))


def create_skill():
    return SleepTracker()

