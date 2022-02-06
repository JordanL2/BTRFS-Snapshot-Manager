#!/usr/bin/python3

from datetime import *


class Period():

    def next_period(last_period):
        raise Exception("This method must be overridden")


class PeriodHour(Period):

    name = 'hourly'
    tag = 'H'
    seconds = 3600

    def next_period(last_period):
        last_period += timedelta(hours=1)
        return last_period.replace(minute=0, second=0, microsecond=0)


class PeriodDay(Period):

    name = 'daily'
    tag = 'D'
    seconds = 86400

    def next_period(last_period):
        last_period += timedelta(days=1)
        return last_period.replace(hour=0, minute=0, second=0, microsecond=0)


class PeriodWeek(Period):

    name = 'weekly'
    tag = 'W'
    seconds = 86400 * 7

    def next_period(last_period):
        last_period += timedelta(days=7)
        return last_period.replace(hour=0, minute=0, second=0, microsecond=0)


class PeriodMonth(Period):

    name = 'monthly'
    tag = 'M'
    seconds = 86400 * 30 # Acceptable estimate, as this is just used for sorting periods by size

    def next_period(last_period):
        year = last_period.year
        month = last_period.month + 1
        if month > 12:
            month = 1
            year += 1
        return last_period.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)


PERIODS = [PeriodHour, PeriodDay, PeriodWeek, PeriodMonth]
PERIOD_TAG_MAP = dict([(p.tag, p) for p in PERIODS])
PERIOD_NAME_MAP = dict([(p.name, p) for p in PERIODS])
