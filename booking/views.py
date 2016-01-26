# -*- coding: utf-8 -*-

import json

from datetime import datetime, timedelta

from dateutil import parser
from dateutil.rrule import rrulestr
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.views.generic import View, TemplateView, ListView, DetailView
from django.utils.translation import ugettext as _
from django.views.generic.edit import UpdateView
from django.views.defaults import bad_request
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect


from profile.models import COORDINATOR, ADMINISTRATOR
from profile.models import role_to_text

from booking.models import Visit, VisitOccurrence, StudyMaterial
from booking.models import Resource, Subject
from booking.models import Room
from booking.models import PostCode, School
from booking.models import Booking
from booking.forms import VisitForm, ClassBookingForm, TeacherBookingForm
from booking.forms import VisitStudyMaterialForm
from booking.forms import BookerForm

i18n_test = _(u"Dette tester oversættelses-systemet")

# A couple of generic superclasses for crud views
# Our views will inherit from these and from django.views.generic classes


class MainPageView(TemplateView):
    """Display the main page."""
    template_name = 'index.html'


class LoginRequiredMixin(object):
    """Include this mixin to require login.

    Mainly useful for users who are not coordinators or administrators.
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check that user is logged in and dispatch."""
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class AccessDenied(PermissionDenied):
    def __init__(self, text, *args, **kwargs):
        _text = text
        print _text
        return super(AccessDenied, self).__init__(text, *args, **kwargs)

    def __unicode__(self):
        print self._text
        return unicode(self._text)


class RoleRequiredMixin(object):
    """Require that user has any of a number of roles."""

    # Roles is a list of required roles - maybe only one.
    # Each user can have only one role, and the condition is fulfilled
    # if one is found.

    roles = []  # Specify in subclass.

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        current_user = self.request.user
        if hasattr(current_user, 'userprofile'):
            role = current_user.userprofile.get_role()
            if role in self.roles:
                return super(RoleRequiredMixin, self).dispatch(*args, **kwargs)
        else:
            pass
        txts = map(role_to_text, self.roles)
        # TODO: Render this with the error message!
        raise AccessDenied(
            u"Kun brugere med disse roller kan logge ind: " +
            u",".join(txts)
        )


class SearchView(ListView):
    """Class for handling main search."""
    model = Resource
    template_name = "resource/searchresult.html"
    context_object_name = "results"
    paginate_by = 10
    base_queryset = None
    filters = None

    def get_base_queryset(self):
        if self.base_queryset is None:
            searchexpression = self.request.GET.get("q", "")
            self.base_queryset = self.model.objects.search(searchexpression)

        return self.base_queryset

    def get_filters(self):
        if self.filters is None:
            self.filters = {}

            # Audience will always include a search for resources marked for
            # all audiences.
            a = self.request.GET.getlist("a")
            if a:
                a.append(Resource.AUDIENCE_ALL)
                self.filters["audience__in"] = a

            t = self.request.GET.getlist("t")
            if t:
                self.filters["type__in"] = t
            f = set(self.request.GET.getlist("f"))
            for g in self.request.GET.getlist("g"):
                f.add(g)
            if f:
                self.filters["subjects__in"] = f
            self.filters["state__in"] = [Resource.ACTIVE]

        return self.filters

    def get_queryset(self):
        filters = self.get_filters()
        return self.get_base_queryset().filter(**filters)

    def make_facet(self, facet_field, choice_tuples, selected,
                   selected_value='checked="checked"',
                   add_to_all=None):

        selected = set(selected)
        hits = {}
        choices = []

        # Remove filter for the field we want to facetize
        new_filters = {}
        for k, v in self.get_filters().iteritems():
            if not k.startswith(facet_field):
                new_filters[k] = v

        qs = self.get_base_queryset().filter(**new_filters)
        qs = qs.values(facet_field).annotate(hits=Count(facet_field))

        for item in qs:
            hits[item[facet_field]] = item["hits"]

        # This adds all hits on a certain keys to the hits of all other keys.
        if add_to_all is not None:
            keys = set(add_to_all)
            to_add = 0

            for key in keys:
                if key in hits:
                    to_add = to_add + hits[key]
                    del hits[key]

            for v, n in choice_tuples:
                if v in keys:
                    continue

                if v in hits:
                    hits[v] += to_add
                else:
                    hits[v] = to_add

        for value, name in choice_tuples:
            if value not in hits:
                continue

            if unicode(value) in selected:
                sel = selected_value
            else:
                sel = ''

            choices.append({
                'label': name,
                'value': value,
                'selected': sel,
                'hits': hits[value]
            })

        return choices

    def get_context_data(self, **kwargs):
        context = {}

        # Store the querystring without the page and pagesize arguments
        qdict = self.request.GET.copy()
        if "page" in qdict:
            qdict.pop("page")
        if "pagesize" in qdict:
            qdict.pop("pagesize")
        context["qstring"] = qdict.urlencode()

        context['pagesizes'] = [5, 10, 15, 20]

        context["audience_choices"] = self.make_facet(
            "audience",
            self.model.audience_choices,
            self.request.GET.getlist("a"),
            add_to_all=[Resource.AUDIENCE_ALL]
        )

        context["type_choices"] = self.make_facet(
            "type",
            self.model.resource_type_choices,
            self.request.GET.getlist("t"),
        )

        gym_subject_choices = []
        gs_subject_choices = []

        for s in Subject.objects.all():
            val = (s.pk, s.name)

            if s.subject_type & Subject.SUBJECT_TYPE_GYMNASIE:
                gym_subject_choices.append(val)

            if s.subject_type & Subject.SUBJECT_TYPE_GRUNDSKOLE:
                gs_subject_choices.append(val)

        gym_selected = self.request.GET.getlist("f")
        context["gymnasie_selected"] = gym_selected
        context["gymnasie_choices"] = self.make_facet(
            "subjects",
            gym_subject_choices,
            gym_selected,
        )

        gs_selected = self.request.GET.getlist("g")
        context["grundskole_selected"] = gs_selected
        context["grundskole_choices"] = self.make_facet(
            "subjects",
            gs_subject_choices,
            gs_selected,
        )

        context.update(kwargs)
        return super(SearchView, self).get_context_data(**context)

    def get_paginate_by(self, queryset):
        return self.request.GET.get("pagesize", 10)


class EditVisit(RoleRequiredMixin, UpdateView):

    template_name = 'visit/form.html'
    form_class = VisitForm
    model = Visit

    # Display a view with two form objects; one for the regular model,
    # and one for the file upload

    roles = COORDINATOR, ADMINISTRATOR

    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        self.object = Visit() if pk is None else Visit.objects.get(id=pk)
        form = self.get_form()
        fileformset = VisitStudyMaterialForm(None, instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, fileformset=fileformset)
        )

    # Handle both forms, creating a Visit and a number of StudyMaterials
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        if not hasattr(self, 'object') or self.object is None:
            self.object = None if pk is None else Visit.objects.get(id=pk)
        form = self.get_form()
        fileformset = VisitStudyMaterialForm(request.POST)
        if form.is_valid():
            visit = form.save()
            if fileformset.is_valid():
                visit.save()

                # Update rooms
                existing_rooms = set([x.name for x in visit.room_set.all()])

                new_rooms = request.POST.getlist("rooms")
                for roomname in new_rooms:
                    if roomname in existing_rooms:
                        existing_rooms.remove(roomname)
                    else:
                        new_room = Room(visit=visit, name=roomname)
                        new_room.save()

                # Delete any rooms left in existing rooms
                if len(existing_rooms) > 0:
                    visit.room_set.all().filter(
                        name__in=existing_rooms
                    ).delete()

                # Attach uploaded files
                for fileform in fileformset:
                    try:
                        instance = StudyMaterial(
                            visit=visit,
                            file=request.FILES["%s-file" % fileform.prefix]
                        )
                        instance.save()
                    except:
                        pass
            # update occurrences
            existing_visit_occurrences = \
                set([x.start_datetime
                     for x in visit.visitoccurrence_set.all()])

            # convert date strings to datetimes
            dates = request.POST.getlist(u'occurrences')

            datetimes = []
            if dates is not None:
                for date in dates:
                    dt = timezone.make_aware(
                        parser.parse(date, dayfirst=True),
                        timezone.pytz.timezone('UTC')
                    )
                    datetimes.append(dt)
            # remove existing to avoid duplicates,
            # then save the rest...
            for date_t in datetimes:
                if date_t in existing_visit_occurrences:
                    existing_visit_occurrences.remove(date_t)
                else:
                    duration = request.POST[u'duration']
                    hours = int(duration[0:2])
                    minutes = int(duration[3:5])
                    end_datetime = date_t
                    if duration is not None:
                        end_datetime = date_t + timedelta(
                            hours=hours,
                            minutes=minutes
                        )
                    instance = VisitOccurrence(
                        start_datetime=date_t,
                        end_datetime1=end_datetime,
                        visit=visit
                    )
                    instance.save()
            # If the set of existing occurrences still is not empty,
            # it means that the user un-ticket one or more existing.
            # So, we remove those to...
            if len(existing_visit_occurrences) > 0:
                visit.visitoccurrence_set.all().filter(
                    start_datetime__in=existing_visit_occurrences
                ).delete()

            return super(EditVisit, self).form_valid(form)
        else:
            return self.form_invalid(form, fileformset)

    def get_context_data(self, **kwargs):
        context = {}

        if self.object and self.object.pk:
            context['rooms'] = self.object.room_set.all()
        else:
            context['rooms'] = []

        search_unit = None
        if self.object and self.object.unit:
            search_unit = self.object.unit
        else:
            if self.request.user and self.request.user.userprofile:
                search_unit = self.request.user.userprofile.unit

        if search_unit is not None:
            context['existingrooms'] = Room.objects.filter(
                visit__unit=search_unit
            ).order_by("name").distinct("name")
        else:
            context['existinrooms'] = []

        context.update(kwargs)

        return super(EditVisit, self).get_context_data(**context)

    def get_success_url(self):
        try:
            return "/visit/%d" % self.object.id
        except:
            return '/'

    def form_invalid(self, form, fileformset=None):
        return self.render_to_response(
            self.get_context_data(form=form, fileformset=fileformset)
        )

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # First, check all is well in superclass
        result = super(EditVisit, self).dispatch(*args, **kwargs)
        # Now, check that the user belongs to the correct unit.
        current_user = self.request.user
        pk = kwargs.get("pk")
        if self.object is None:
            self.object = None if pk is None else Visit.objects.get(id=pk)
        if self.object is not None:
            role = current_user.userprofile.get_role()
            if role == COORDINATOR:
                users_unit = current_user.userprofile.unit
                visits_unit = self.object.unit
                if visits_unit and not visits_unit.belongs_to(users_unit):
                    raise AccessDenied(
                        _(u"Du kan kun redigere enheder,som du selv er" +
                          " koordinator for.")
                    )
        return result

    def get_form_kwargs(self):
        kwargs = super(EditVisit, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class VisitDetailView(DetailView):
    """Display Visit details"""
    model = Visit
    template_name = 'visit/details.html'

    def get_queryset(self):
        """Get queryset, only include active visits."""
        qs = super(VisitDetailView, self).get_queryset()
        # Dismiss visits that are not active.
        if not self.request.user.is_authenticated():
            qs = qs.filter(state=Resource.ACTIVE)
        return qs


class RrulestrView(View):

    def post(self, request):
        """
        Handle Ajax requests: Essentially, dateutil.rrule.rrulestr function
        exposed as a web service, expanding RRULEs to a list of datetimes.
        In addition, we add RRDATEs and return the sorted list in danish
        date format. If the string doesn't contain an UNTIL clause, we set it
        to 90 days in the future from datetime.now().
        If multiple start_times are present, the Cartesian product of
        dates x start_times is returned.
        """
        rrulestring = request.POST['rrulestr']
        now = timezone.now()
        tz = timezone.pytz.timezone('UTC')
        dates = []
        lines = rrulestring.split("\n")
        times_list = request.POST[u'start_times'].split(',')
        visit_id = None
        if request.POST[u'visit_id'] != 'None':
            visit_id = int(request.POST[u'visit_id'])
        existing_dates_strings = set()

        if visit_id is not None:
            visit = Visit.objects.get(pk=visit_id)

            for occurrence in visit.visitoccurrence_set.all():
                existing_dates_strings.add(
                    occurrence.start_datetime.strftime('%d-%m-%Y %H:%M')
                )

        for line in lines:
            # When handling RRULEs, we don't want to send all dates until
            # 9999-12-31 to the client, which apparently is rrulestr() default
            # behaviour. Hence, we set a default UNTIL clause to 90 days in
            # the future from datetime.now()
            # Todo: This should probably be handled more elegantly
            if u'RRULE' in line and u'UNTIL=' not in line:
                line += u';UNTIL=%s' % (now + timedelta(90))\
                    .strftime('%Y%m%dT%H%M%SZ')
                dates = [timezone.make_aware(x, tz)
                         for x in rrulestr(line, ignoretz=True)]
            # RRDATEs are appended to the dates list
            elif u'RDATE' in line:
                dates.append(datetime.strptime(line[6:], '%Y%m%dT%H%M%SZ'))
        # sort the list while still in ISO 8601 format,
        dates.sort()
        # Cartesian product: AxB
        # ['2016-01-01','2016-01-02'] x ['10:00','12:00'] ->
        # ['2016-01-01 10:00','2016-01-01 12:00',
        # '2016-01-02 10:00','2016-01-02 12:00']
        cartesian_dates = \
            [val.replace(  # parse time format: '00:00'
                hour=int(_[0:2]),
                minute=int(_[4:6]),
                second=0,
                microsecond=0
            ) for val in dates for _ in times_list]

        # convert to danish date format strings and off we go...
        date_strings = [x.strftime('%d-%m-%Y %H:%M') for x in cartesian_dates]

        dates_without_existing_dates = \
            [x for x in date_strings if x not in existing_dates_strings]
        return HttpResponse(
            json.dumps(dates_without_existing_dates),
            content_type='application/json'
        )


class AdminIndexView(MainPageView):
    template_name = 'admin_index.html'


class AdminSearchView(SearchView):
    template_name = 'resource/admin_searchresult.html'


class AdminVisitDetailView(VisitDetailView):
    template_name = 'visit/admin_details.html'


class PostcodeView(View):
    def get(self, request, *args, **kwargs):
        code = int(kwargs.get("code"))
        postcode = PostCode.get(code)
        city = postcode.city if postcode is not None else None
        region = {'id': postcode.region.id, 'name': postcode.region.name} \
            if postcode is not None else None
        return JsonResponse({'code': code, 'city': city, 'region': region})


class SchoolView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET['q']
        items = School.search(query)
        json = {'schools':
                [
                    {'name': item.name,
                     'postcode': item.postcode.number} for item in items
                ]
                }
        return JsonResponse(json)


class BookingView(UpdateView):

    visit = None

    def set_visit(self, visit_id):
        if visit_id is not None:
            try:
                self.visit = Visit.objects.get(id=visit_id)
            except:
                pass

    def get_visit_type(self):
        if self.visit is None:
            return None
        if self.visit.type == Resource.STUDENT_FOR_A_DAY:
            return
        if self.visit.type == Resource.STUDY_PROJECT:
            return
        if self.visit.audience == Resource.AUDIENCE_TEACHER:
            return
        if self.visit.audience == Resource.AUDIENCE_STUDENT:
            return

    def get(self, request, *args, **kwargs):
        self.set_visit(kwargs.get("visit"))
        if self.visit is None:
            return bad_request(request)

        data = {'visit': self.visit}

        self.object = Booking()
        data.update(self.get_forms())
        return self.render_to_response(
            self.get_context_data(**data)
        )

    def post(self, request, *args, **kwargs):
        self.set_visit(kwargs.get("visit"))
        if self.visit is None:
            return bad_request(request)

        data = {'visit': self.visit}

        self.object = Booking()
        forms = self.get_forms(request.POST)
        valid = True
        for (name, form) in forms.items():
            if not form.is_valid():
                valid = False

        if valid:
            if 'bookingform' in forms:
                booking = forms['bookingform'].save(commit=False)
            else:
                booking = self.object
            booking.visit = self.visit
            if 'bookerform' in forms:
                booking.booker = forms['bookerform'].save()
            booking.save()
            return redirect("/visit/%d/book/success" % self.visit.id)

        data.update(forms)
        return self.render_to_response(
            self.get_context_data(**data)
        )

    def get_forms(self, data=None):
        forms = {}
        if self.visit is not None:
            forms['bookerform'] = BookerForm(data, visit=self.visit)

            if self.visit.type == Resource.GROUP_VISIT:
                forms['bookingform'] = ClassBookingForm(data, visit=self.visit)
            if self.visit.audience == Resource.AUDIENCE_TEACHER:
                forms['bookingform'] = TeacherBookingForm(data,
                                                          visit=self.visit)
        return forms

    def get_template_names(self):
        if self.visit is None:
            return [""]
        if self.visit.type == Resource.STUDENT_FOR_A_DAY:
            return ["booking/studentforaday.html"]
        if self.visit.type == Resource.STUDY_PROJECT:
            return ["booking/srp.html"]
        if self.visit.audience == Resource.AUDIENCE_TEACHER:
            return ["booking/teachervisit.html"]
        if self.visit.audience == Resource.AUDIENCE_STUDENT:
            return ["booking/classvisit.html"]


class BookingSuccessView(TemplateView):
    template_name = "booking/success.html"

    def get(self, request, *args, **kwargs):
        visit_id = kwargs.get("visit")
        visit = None
        if visit_id is not None:
            try:
                visit = Visit.objects.get(id=visit_id)
            except:
                pass
        if visit is None:
            return bad_request(request)

        data = {'visit': visit}

        return self.render_to_response(
            self.get_context_data(**data)
        )
