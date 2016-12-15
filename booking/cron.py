from datetime import timedelta, date

from booking.models import VisitAutosend, EmailTemplateType, Visit
from booking.models import MultiProductVisitTemp
from booking.models import EventTime
from django_cron import CronJobBase, Schedule
from django.db.models import Count
from django.utils import timezone

import traceback


class KuCronJob(CronJobBase):

    description = "base KU cron job"

    def run(self):
        pass

    def do(self):
        print "---------------------------------------------------------------"
        print "[%s] Beginning %s (%s)" % (
            unicode(timezone.now()),
            self.__class__.__name__,
            self.description
        )
        try:
            self.run()
            print "CRON job complete"
        except:
            print traceback.format_exc()
            print "CRON job failed"
            raise


class ReminderJob(KuCronJob):
    RUN_AT_TIMES = ['01:00']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'kubooking.reminders'
    description = "sends reminder emails"

    def run(self):
        autosends = list(VisitAutosend.objects.filter(
            enabled=True,
            template_type=EmailTemplateType.get(
                EmailTemplateType.NOTITY_ALL__BOOKING_REMINDER
            ),
            days__isnull=False,
            inherit=False
        ).all())
        print "Found %d enabled autosends" % len(autosends)

        inheriting_autosends = list(VisitAutosend.objects.filter(
            inherit=True,
            template_type=EmailTemplateType.get(
                EmailTemplateType.NOTITY_ALL__BOOKING_REMINDER
            ),
        ).all())

        extra = []
        for autosend in inheriting_autosends:
            inherited = autosend.get_inherited()
            if inherited is not None and \
                    inherited.enabled and \
                    inherited.days is not None:
                autosend.days = inherited.days
                autosend.enabled = inherited.enabled
                extra.append(autosend)
        print "Found %d enabled inheriting autosends" % len(extra)
        autosends.extend(extra)

        if len(autosends) > 0:
            today = date.today()
            print "Today is: %s" % unicode(today)

            for autosend in autosends:
                if autosend is not None:
                    print "Autosend %d for Visit %d:" % \
                        (autosend.id, autosend.visit.id)
                    print "    Visit starts on %s" % \
                        unicode(autosend.visit.start_datetime.date())
                    reminderday = autosend.visit.\
                        start_datetime.date() - \
                        timedelta(autosend.days)
                    print "    Autosend specifies to send %d " \
                          "days prior, on %s" % (autosend.days, reminderday)
                    if reminderday == today:
                        print "    That's today; send reminder now"
                        autosend.visit.autosend(
                            EmailTemplateType.get(
                                EmailTemplateType.NOTITY_ALL__BOOKING_REMINDER
                            )
                        )
                    else:
                        print "    That's not today. Not sending reminder"


class IdleHostroleJob(KuCronJob):
    RUN_AT_TIMES = ['01:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'kubooking.idlehost'
    description = "sends notification emails regarding idle host roles"

    def run(self):

        visit_qs = Visit.objects.annotate(
            num_bookings=Count('bookings'),
        ).filter(
            num_bookings__gt=0,
            workflow_status=Visit.WORKFLOW_STATUS_BEING_PLANNED
        )
        visits_needing_hosts = [
            visit for visit in visit_qs if visit.needs_hosts
        ]

        autosends = list(VisitAutosend.objects.filter(
            enabled=True,
            template_type=EmailTemplateType.get(
                EmailTemplateType.NOTIFY_HOST__HOSTROLE_IDLE
            ),
            days__isnull=False,
            inherit=False,
            visit__in=visits_needing_hosts
        ).all())
        print "Found %d enabled autosends" % len(autosends)

        inheriting_autosends = list(VisitAutosend.objects.filter(
            inherit=True,
            template_type=EmailTemplateType.get(
                EmailTemplateType.NOTIFY_HOST__HOSTROLE_IDLE
            ),
            visit__in=visits_needing_hosts
        ).all())

        extra = []
        for autosend in inheriting_autosends:
            inherited = autosend.get_inherited()
            if inherited is not None and \
                    inherited.enabled and \
                    inherited.days is not None:
                autosend.days = inherited.days
                autosend.enabled = inherited.enabled
                extra.append(autosend)
        print "Found %d enabled inheriting autosends" % len(extra)
        autosends.extend(extra)

        if len(autosends) > 0:
            today = date.today()
            print "Today is: %s" % unicode(today)

            for autosend in autosends:
                if autosend is not None:
                    print "Autosend %d for Visit %d:" % \
                          (autosend.id, autosend.visit.id)
                    first_booking = autosend.visit.\
                        bookings.earliest('statistics__created_time')
                    print "    Visit has its first booking on %s" % \
                          unicode(first_booking.statistics.created_time.date())

                    alertday = first_booking.statistics.created_time.date() + \
                        timedelta(autosend.days)
                    print "    Autosend specifies to send %d days after " \
                          "first booking, on %s" % (autosend.days, alertday)
                    if alertday == today:
                        print "    That's today; send alert now"
                        try:
                            autosend.visit.autosend(
                                EmailTemplateType.get(
                                    EmailTemplateType.
                                    NOTIFY_HOST__HOSTROLE_IDLE
                                )
                            )
                        except Exception as e:
                            print e
                    else:
                        print "    That's not today. Not sending alert"


class RemoveOldMvpJob(KuCronJob):
    RUN_AT_TIMES = ['01:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'kubooking.removempv'
    description = "deletes obsolete mvp temps"

    def run(self):
        MultiProductVisitTemp.objects.filter(
            updated__lt=timezone.now()-timedelta(days=1)
        ).delete()


class NotifyEventTimeJob(KuCronJob):
    RUN_EVERY_MINS = 1
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'kubooking.notifyeventtime'
    description = "notifies EventTimes that they're starting/ending"

    def run(self):
        start = timezone.now().replace(second=0, microsecond=0)
        next = start + timedelta(minutes=1)

        for eventtime in EventTime.objects.filter(
                has_notified_start=False,
                start__gte=start,
                start__lt=next
        ):
            eventtime.on_start()

        for eventtime in EventTime.objects.filter(
                has_notified_end=False,
                end__gte=start,
                end__lt=next
        ):
            eventtime.on_end()
