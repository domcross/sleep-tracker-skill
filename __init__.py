from mycroft import MycroftSkill, intent_file_handler


class SleepTracker(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('tracker.sleep.intent')
    def handle_tracker_sleep(self, message):
        self.speak_dialog('tracker.sleep')


def create_skill():
    return SleepTracker()

