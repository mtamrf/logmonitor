
import datetime
from .logparser import LINE_DATA_FIELDS
from .utils import enum

MESSAGE_TYPES = enum('summary', 'alert')

class Message(object):
    """Messages sent to Displays by Notifiers"""
    def __init__(self, lines, type):
        super(Message, self).__init__()
        self.lines = lines
        self.type = type

class BaseNotifier(object):
    def __init__(self, display):
        super(BaseNotifier, self).__init__()
        self.display = display

    def insert_data(self, data):
        raise NotImplementedError(self.__class__.__name__ + '.insert_data')
    
    @property
    def message(self):
        raise NotImplementedError(self.__class__.__name__ + '.message')

    def notify(self): 
        self.display.show(self.message)


class SectionNotifier(BaseNotifier):
    def __init__(self, display):
        BaseNotifier.__init__(self, display)
        self.section_2_hits = {}

    def insert_data(self, linedata):
        section = linedata[LINE_DATA_FIELDS.section]
        self.section_2_hits[section] = self.section_2_hits.get(section, 0) + 1

    @property
    def message(self):
        result = self.section_2_hits.copy()
        self.section_2_hits = {}
        lines = ["section stats",
                 result]
        message = Message(lines, MESSAGE_TYPES.summary)
        return message


class AlertNotifier(BaseNotifier):
    def __init__(self, display, interval, hits_threshold):
        BaseNotifier.__init__(self, display)
        self._interval = datetime.timedelta(seconds=interval)
        self.hits_threshold = hits_threshold
        # time of last event inserted
        self._last_event_time = datetime.datetime.now()
        self._time_2_hits = {}
        self.hits = 0
        self.is_alert_displayed = False
    
    def insert_data(self, linedata):
        event_time = linedata[LINE_DATA_FIELDS.datetime]
        # purge old data (determined by interval)
        if event_time > self._last_event_time:
            self._last_event_time = event_time
            for time, hits in self._time_2_hits.items():
                if time + self._interval < event_time:
                    self.hits -= hits
                    del self._time_2_hits[time]
        self._time_2_hits[event_time] = self._time_2_hits.get(event_time, 0) + 1
        self.hits += 1

    @property
    def message(self):    
        lines = []
        #print 'HITS:', self.hits
        if self.hits > self.hits_threshold:
            if not self.is_alert_displayed:
                self.is_alert_displayed = True
                lines.append(self.high_traffic_message(self.hits, self._last_event_time))
        elif self.is_alert_displayed:
            self.is_alert_displayed = False
            lines.append(self.recovered_message(self._last_event_time))
        message = Message(lines, MESSAGE_TYPES.alert)
        return message

    def high_traffic_message(self, hits, time):
        message = "High traffic generated an alert - hits = %i, triggered at %s" % (hits, time)
        return message

    def recovered_message(self, time):
        message = "alert recovered at %s" % (time)
        return message
