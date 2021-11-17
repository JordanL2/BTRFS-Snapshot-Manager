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
        return last_period + timedelta(hours=1)


class PeriodDay(Period):

    name = 'daily'
    tag = 'D'
    seconds = 86400

    def next_period(last_period):
        return last_period + timedelta(days=1)


class PeriodWeek(Period):

    name = 'weekly'
    tag = 'W'
    seconds = 86400 * 7

    def next_period(last_period):
        return last_period + timedelta(days=7)


class PeriodMonth(Period):

    name = 'monthly'
    tag = 'M'
    seconds = 86400 * 30 # Acceptable estimate, as this is just used for sorting periods by size

    def next_period(last_period):
        month = last_period.month
        year = last_period.year
        month += 1
        if month > 12:
            month = 1
            year += 1
        return last_period.replace(month=month, year=year)


periods = [PeriodHour, PeriodDay, PeriodWeek, PeriodMonth]
period_map = dict([(p.tag, p) for p in periods])
period_name_map = dict([(p.name, p) for p in periods])
periods_max_name_length = max([len(p.name) for p in periods])
