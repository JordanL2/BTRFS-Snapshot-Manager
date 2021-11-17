#!/usr/bin/python3


class Period():

    def period_passed(t1, t2):
        raise Exception("This method must be overridden")


class PeriodHour(Period):

    name = 'hourly'
    tag = 'H'

    def period_passed(t1, t2):
        #TODO
        return False


class PeriodDay(Period):

    name = 'daily'
    tag = 'D'

    def period_passed(t1, t2):
        #TODO
        return False


class PeriodWeek(Period):

    name = 'weekly'
    tag = 'W'

    def period_passed(t1, t2):
        #TODO
        return False


class PeriodMonth(Period):

    name = 'monthly'
    tag = 'M'

    def period_passed(t1, t2):
        #TODO
        return False


periods = [PeriodHour, PeriodDay, PeriodWeek, PeriodMonth]
period_map = dict([(p.tag, p) for p in periods])
