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
# TODO - return error if object is not a datetime object
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
        # Initialize, including birthdate from skill settings and the database table
        MycroftSkill.__init__(self)
        self.dbconn = BufordSQLite(self.file_system.path)
        birth_year = self.settings.get("year", "")
        birth_month = self.settings.get("month", "")
        birth_day = self.settings.get("day", "")
        self.birthdate = datetime(year = int(birth_year), month = int(birth_month), day = int(birth_day))
        table_query = "CREATE TABLE IF NOT EXISTS sleep_records (record_id INTEGER NOT NULL PRIMARY KEY, sleep_start TEXT NOT NULL, sleep_end TEXT, invalidated INTEGER NOT NULL DEFAULT 0)"
        self.dbconn.emptyQuery(table_query)
        self.dbconn.commit()
        #LOG.debug(self.settings)

    def initialize(self):
        self.register_intent_file('tracker.sleep.intent', self.handle_tracker_sleep)
        self.register_intent_file('tracker.wakeup.intent', self.handle_tracker_wakeup)

    # DATABASE - creates a new sleep record
    def openSleepRecord():
        openRecordQuery = "INSERT INTO sleep_records (sleep_start) VALUES ('" + datetime_to_BufordSQLiteString(datetime.now()) + "')"
        self.dbconn.emptyQuery(openRecordQuery)
        self.dbconn.commit()

    # DATABASE - checks for a previously open sleep record. Can be used when attempting to create a record via voice
    def checkUnclosedSleepRecord():
        unclosedRecordsQuery = "SELECT record_id FROM sleep_records WHERE sleep_end IS NULL AND invalidated = 0"
        return self.dbconn.returnQuery(unclosedRecordsQuery, return_type="Table")

    # DATABASE - Automatically invalidates any sleep records that were forgot to close after 24 hours.
    # Sleep records should be closed the moment the user wakes up.
    def invalidateBeyond24Hours():
        unclosedRecordsQuery = "SELECT record_id, sleep_start FROM sleep_records WHERE sleep_end IS NULL AND invalidated = 0"
        current_time = datetime.now()
        openRecords = self.dbconn.returnQuery(unclosedRecordsQuery, return_type="Table")
        for record in openRecords:
            sleep_time = bufordSQLiteString_to_datetime(record[1])
            differences = current_time - sleep_time
            differences_days = differences.days
            if differences_days >= 1:
                updateInvalidateQuery = "UPDATE sleep_records SET invalidated = 1 WHERE record_id = " + str(record[0]) + ""
                self.dbconn.emptyQuery(updateInvalidateQuery)
                self.dbconn.commit()

    # DATABASE - Closes the sleep record.
    # This ensures that the number of hours can be obtained
    # Calculations are performed database-wide instead of manually recording the number of hours
    # TODO - Return error if there are no open sleep records
    def closeSleepRecord():
        # Checks for an open, non-invalidated record
        unclosedRecordsQuery = "SELECT record_id, sleep_start FROM sleep_records WHERE sleep_end IS NULL AND invalidated = 0"
        record_to_be_closed = self.dbconn.returnQuery(unclosedRecordsQuery, return_type="Columns")
        # Gets sleep time
        sleep_time = bufordSQLiteString_to_datetime(record_to_be_closed[1]) 
        # Wakeup time is now -- it is when the user tells Mycroft that they are awake
        wakeup_time = datetime.now()
        # Gets the number of hours slept
        differences = current_time - sleep_time
        differences_days = differences.days
        # Gets the most recent open sleep record, and adds the sleep_end time to mark the record as closed.
        if differences_days < 1:
            updateInvalidateQuery = "UPDATE sleep_records SET sleep_end = '" + datetime_to_BufordSQLiteString(wakeup_time) + "' WHERE record_id = " + str(record_to_be_closed[0])
            self.dbconn.emptyQuery(updateInvalidateQuery)
            self.dbconn.commit()
            differences_str = str(differences)
            differences_list = differences_str.split(':')
            # Returns the number of hours in string format, to avoid string conversions on the Mycroft response.
            return differences_list[0]

    # MYCROFT - allows user to start the sleep tracker.
    # This calls the openSleepRecord method.
    # TODO - error if a record is still unopen and is below 24 hours.
    @intent_file_handler('tracker.sleep.intent')
    def handle_tracker_sleep(self, message):
        # Invalidating sleep records beyond 24 hours
        self.invalidateBeyond24Hours()
        # Creates a new sleep record
        self.openSleepRecord()
        # Reminds user that the sleep tracker is started
        self.speak_dialog('tracker.sleep')

    # MYCROFT - allows user to stop the sleep tracker.
    # This calls the closeSleepRecord method.
    # TODO - error if there are no open sleep records.
    @intent_file_handler('tracker.wakeup.intent')
    def handle_tracker_wakeup(self, message):
        num_hours = self.closeSleepRecord()
        self.speak("You have slept for " + num_hours + "hours.")

def create_skill():
    return SleepTracker()

