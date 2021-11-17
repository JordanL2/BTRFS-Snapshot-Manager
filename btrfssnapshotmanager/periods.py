#!/usr/bin/python3


class Period():

    def period_passed(t1, t2):
        raise Exception("This method must be overridden")


class PeriodHour(Period):

    name = 'hourly'
    tag = 'H'
    seconds = 3600

    def period_passed(t1, t2):
        #TODO
        return False


class PeriodDay(Period):

    name = 'daily'
    tag = 'D'
    seconds = 86400

    def period_passed(t1, t2):
        #TODO
        return False


class PeriodWeek(Period):

    name = 'weekly'
    tag = 'W'
    seconds = 86400 * 7

    def period_passed(t1, t2):
        #TODO
        return False


class PeriodMonth(Period):

    name = 'monthly'
    tag = 'M'
    seconds = 86400 * 30

    def period_passed(t1, t2):
        #TODO
        return False


periods = [PeriodHour, PeriodDay, PeriodWeek, PeriodMonth]
period_map = dict([(p.tag, p) for p in periods])
