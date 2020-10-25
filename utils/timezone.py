"""
Implements timezone handling as required by ReMoni.

:synopsis: Stamp measurements with Zulu time (UTC), and easy future-proof management of timestamps.
:author: Janus Bo Andersen.
:date: October 2020.

:Description:
Output dates in ISO 8601 format, i.e. output 2020-10-25T10:08:00Z
for 25th October 2020 at 10:08:00 (HH:MM:SS) in UTC time.

Note that ISO 8601 allows using +00:00 instead of Z.
ReMoni prefers Z for this implementation.

UTC class implementation based on: https://docs.python.org/3.5/library/datetime.html
Zulu time definition based on: https://en.wikipedia.org/wiki/ISO_8601

"""

from datetime import tzinfo, timedelta, datetime


class ZuluTime(tzinfo):
    """
    Very explicit Zulu-time class to implement Zulu time is UTC time.
    Implements required methods on abstract base class tzinfo.
    Can be modified if needed.
    """

    # Easy-reading constants
    ZERO = timedelta(0)
    HOUR = timedelta(hours=1)

    def utcoffset(self, dt):
        """
        UTC is zero time offset from UTC, of course.
        """
        return self.ZERO

    def tzname(self, dt):
        """
        Name of timezone.
        """
        return "UTC"

    def dst(self, dt):
        """
        No Daylight savings time.
        """
        return self.ZERO


def zulu_time_str(timestamp: datetime) -> str:
    """
    Print a timestamp with ISO format like 2020-10-25T10:08:00Z
    """

    # ISO 8601 format with the Z specifier for a textual time stamp
    iso8601_format = "%Y-%m-%dT%H:%M:%SZ"

    return timestamp.strftime(iso8601_format)
