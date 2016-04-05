from django.db.models.signals import post_save
from booking.models import Booker
from booking.models import Booking, ClassBooking, TeacherBooking
from booking.models import Resource, Visit, OtherResource
from booking.models import VisitOccurrence

MODELS_WITH_SEARCHINDEX = set([
    Resource,
    Visit,
    OtherResource,
    VisitOccurrence
])

BOOKING_MODELS = set([
    Booking,
    ClassBooking,
    TeacherBooking
])


def run_searchindex_for_object(obj):
    t = type(obj)

    if t in MODELS_WITH_SEARCHINDEX:
        # Disconnect signal to avoid recursion
        post_save.disconnect(update_search_indexes, sender=t)
        # Run the indexing
        obj.update_searchindex()
        # Re-enable signal
        post_save.connect(update_search_indexes, sender=t)


def update_search_indexes(sender, instance, **kwargs):
    run_searchindex_for_object(instance)

for x in MODELS_WITH_SEARCHINDEX:
    post_save.connect(update_search_indexes, sender=x)


def on_booking_save(sender, instance, **kwargs):
    vo = getattr(instance, 'visitoccurrence', None)
    if vo:
        run_searchindex_for_object(vo)

for x in BOOKING_MODELS:
    post_save.connect(on_booking_save, sender=x)


def on_booker_save(sender, instance, **kwargs):
    for x in instance.booking_set.all():
        vo = getattr(x, 'visitoccurrence', None)
        if vo:
            run_searchindex_for_object(vo)

post_save.connect(on_booker_save, sender=Booker)