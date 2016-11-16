# -*- coding: utf-8 -*-

from booking.models import StudyMaterial, ProductAutosend, Booking
from booking.models import Subject, BookingGrundskoleSubjectLevel
from booking.models import Locality, OrganizationalUnitType, OrganizationalUnit
from booking.models import Product
from booking.models import Guest, Region, PostCode, School
from booking.models import ClassBooking, TeacherBooking, \
    BookingGymnasieSubjectLevel
from booking.models import EmailTemplate, EmailTemplateType
from booking.models import Visit, MultiProductVisitTemp
from booking.models import BLANK_LABEL, BLANK_OPTION
from booking.widgets import OrderedMultipleHiddenChooser
from booking.utils import binary_or, binary_and
from django import forms
from django.db.models import Q
from django.db.models.expressions import OrderBy
from django.forms import CheckboxSelectMultiple, CheckboxInput
from django.forms import EmailInput
from django.forms import formset_factory, inlineformset_factory
from django.forms import TextInput, NumberInput, DateInput, Textarea, Select
from django.forms import HiddenInput
from django.utils.translation import ugettext_lazy as _
from tinymce.widgets import TinyMCE
from .fields import ExtensibleMultipleChoiceField


class AdminProductSearchForm(forms.Form):

    q = forms.CharField(
        label=_(u'Fritekst'),
        max_length=60,
        required=False
    )

    s = forms.ChoiceField(
        label=_(u'Status'),
        choices=(('', _(u'[Vælg status]')),) + Product.state_choices,
        required=False
    )

    e = forms.ChoiceField(
        label=_(u'Tilbud er aktivt'),
        choices=(
            (None, _(u'[Vælg]')),
            (1, _(u'Ja')),
            (0, _(u'Nej')),
        ),
        required=False
    )

    IS_VISIT = 1
    IS_NOT_VISIT = 2

    v = forms.ChoiceField(
        label=_(u'Besøg / ikke besøg'),
        choices=(
            (None, _(u'[Vælg]')),
            (IS_VISIT, _(u'Tilbud med besøg')),
            (IS_NOT_VISIT, _(u'Tilbud uden besøg')),
        ),
        required=False
    )

    HAS_BOOKINGS = 1
    HAS_NO_BOOKINGS = 2

    b = forms.ChoiceField(
        label=_(u'Bookinger'),
        choices=(
            (None, _(u'[Vælg]')),
            (HAS_BOOKINGS, _(u'Tilbud der har bookinger')),
            (HAS_NO_BOOKINGS, _(u'Tilbud der ikke har bookinger')),
        ),
        required=False
    )

    MY_UNIT = -1
    MY_FACULTY = -2
    MY_UNITS = -3

    u = forms.ChoiceField(
        label=_(u'Enhed'),
        required=False
    )

    to_date = forms.DateField(
        label=_(u'Dato til'),
        required=False
    )

    from_date = forms.DateField(
        label=_(u'Dato fra'),
        required=False
    )

    def __init__(self, qdict, *args, **kwargs):
        self.user = kwargs.pop("user")

        super(AdminProductSearchForm, self).__init__(qdict, *args, **kwargs)

        self.fields['u'].choices = self.get_unit_choices()

        extra_classes = {
            'from_date': 'datepicker datepicker-admin',
            'to_date': 'datepicker datepicker-admin'
        }

        # Add classnames to all fields
        for fname, f in self.fields.iteritems():
            f.widget.attrs['class'] = " ".join([
                x for x in (
                    f.widget.attrs.get('class'),
                    'form-control input-sm',
                    extra_classes.get(fname)
                ) if x
            ])

        self.hiddenfields = []
        for x in ("a", "t", "f", "g", "i"):
            for y in qdict.getlist(x, []):
                self.hiddenfields.append((x, y,))

    def get_unit_choices(self):
        choices = [
            (None, _(u'[Vælg]')),
            (self.MY_UNIT, _(u'Tilbud under min enhed')),
            (self.MY_FACULTY, _(u'Tilbud under mit fakultet')),
            (
                self.MY_UNITS,
                _(u'Tilbud under alle enheder jeg kan administrere')
            ),
            (None, '======'),
        ]

        for x in self.user.userprofile.get_unit_queryset():
            choices.append((x.pk, unicode(x)))

        return choices

    def add_prefix(self, field_name):
        # Remove _date postfix from date fields
        if field_name in ('from_date', 'to_date'):
            field_name = field_name[:-5]

        return super(AdminProductSearchForm, self).add_prefix(field_name)


class VisitSearchForm(forms.Form):
    q = forms.CharField(
        label=_(u'Fritekst'),
        max_length=60,
        required=False
    )

    t = forms.CharField(
        label=_(u'Tilbuds-ID'),
        max_length=10,
        required=False,
        widget=forms.widgets.NumberInput
    )

    MY_UNIT = -1
    MY_FACULTY = -2
    MY_UNITS = -3

    u = forms.ChoiceField(
        label=_(u'Enhed'),
        required=False
    )

    WORKFLOW_STATUS_PENDING = -1
    WORKFLOW_STATUS_READY = -2

    w = forms.ChoiceField(
        label=_(u'Workflow status'),
        choices=(
            ('', _(u'Alle')),
            (WORKFLOW_STATUS_PENDING, _(u'Alle ikke-planlagte')),
            (WORKFLOW_STATUS_READY, _(u'Alle planlagte')),
            ('', u'====='),
        ) + Visit.workflow_status_choices,
        required=False
    )

    participant_choices = (
        ('', _(u'[Vælg]')),
        (1, 1),
        (5, 5),
    ) + tuple((x, x) for x in range(10, 60, 10))

    p_min = forms.ChoiceField(
        label=_(u'Minimum antal deltagere'),
        choices=participant_choices,
        required=False
    )

    p_max = forms.ChoiceField(
        label=_(u'Maksimum antal deltagere'),
        choices=participant_choices,
        required=False
    )

    from_date = forms.DateField(
        label=_(u'Dato fra'),
        input_formats=['%d-%m-%Y'],
        required=False
    )

    to_date = forms.DateField(
        label=_(u'Dato til'),
        input_formats=['%d-%m-%Y'],
        required=False
    )

    def __init__(self, qdict, *args, **kwargs):
        self.user = kwargs.pop("user")

        qdict = qdict.copy()

        # Set some defaults if form was not submitted
        if not qdict.get("go", False):
            if qdict.get("u", "") == "":
                qdict["u"] = self.MY_UNITS

            if qdict.get("s", "") == "":
                qdict["s"] = Product.ACTIVE

        super(VisitSearchForm, self).__init__(qdict, *args, **kwargs)

        self.fields['u'].choices = self.get_unit_choices()

        extra_classes = {
            'from_date': 'datepicker datepicker-admin',
            'to_date': 'datepicker datepicker-admin'
        }

        # Add classnames to all fields
        for fname, f in self.fields.iteritems():
            f.widget.attrs['class'] = " ".join([
                x for x in (
                    f.widget.attrs.get('class'),
                    'form-control input-sm',
                    extra_classes.get(fname)
                ) if x
            ])

    def get_unit_choices(self):
        choices = [
            (None, _(u'[Vælg]')),
            (self.MY_UNIT, _(u'Tilbud under min enhed')),
            (self.MY_FACULTY, _(u'Tilbud under mit fakultet')),
            (
                self.MY_UNITS,
                _(u'Tilbud under alle enheder jeg kan administrere')
            ),
            (None, '======'),
        ]

        for x in self.user.userprofile.get_unit_queryset():
            choices.append((x.pk, unicode(x)))

        return choices


class OrganizationalUnitTypeForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnitType
        fields = ('name',)


class OrganizationalUnitForm(forms.ModelForm):
    class Meta:
        model = OrganizationalUnit
        fields = ('name', 'type', 'parent')


class ProductInitialForm(forms.Form):
    type = forms.ChoiceField(
        choices=Product.resource_type_choices
    )


class ProductForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = Product
        fields = ('title', 'teaser', 'description', 'price', 'state',
                  'type', 'tags',
                  'institution_level', 'topics', 'audience',
                  'minimum_number_of_visitors', 'maximum_number_of_visitors',
                  'do_create_waiting_list', 'waiting_list_length',
                  'waiting_list_deadline_days', 'waiting_list_deadline_hours',
                  'time_mode', 'duration', 'locality',
                  'tour_available', 'catering_available',
                  'presentation_available', 'custom_available', 'custom_name',
                  'tilbudsansvarlig', 'organizationalunit',
                  'preparation_time', 'comment',
                  )

        widgets = {
            'title': TextInput(attrs={
                'class': 'titlefield form-control input-sm',
                'rows': 1, 'size': 62
            }),
            'teaser': Textarea(
                attrs={
                    'class': 'form-control input-sm',
                    'rows': 3,
                    'cols': 70,
                    'maxlength': 210
                }
            ),
            'description': TinyMCE(),
            'custom_name': TextInput(attrs={
                'class': 'titlefield form-control input-sm',
                'rows': 1, 'size': 62
            }),

            'price': NumberInput(attrs={'class': 'form-control input-sm'}),
            'type': Select(attrs={'class': 'form-control input-sm'}),
            'preparation_time': Textarea(
                attrs={'class': 'form-control input-sm'}
            ),
            'comment': Textarea(attrs={'class': 'form-control input-sm'}),
            'institution_level': Select(
                attrs={'class': 'form-control input-sm'}
            ),
            'minimum_number_of_visitors': NumberInput(
                attrs={'class': 'form-control input-sm', 'min': 1}
            ),
            'maximum_number_of_visitors': NumberInput(
                attrs={'class': 'form-control input-sm', 'min': 1}
            ),
            'do_create_waiting_list': CheckboxInput(
                attrs={
                    'class': 'form-control input-sm',
                    'data-toggle': 'hide',
                    'data-target': '!.waitinglist-dependent'
                }
            ),
            'waiting_list_length': NumberInput(
                attrs={
                    'class': 'form-control input-sm waitinglist-dependent',
                    'min': 1
                }
            ),
            'waiting_list_deadline_days': NumberInput(
                attrs={
                    'class': 'form-control input-sm waitinglist-dependent',
                    'min': 0
                }
            ),
            'waiting_list_deadline_hours': NumberInput(
                attrs={
                    'class': 'form-control input-sm waitinglist-dependent',
                    'min': 0,
                    'max': 23
                }
            ),
            'duration': Select(attrs={'class': 'form-control input-sm'}),
            'locality': Select(attrs={'class': 'form-control input-sm'}),
            'organizationalunit': Select(
                attrs={'class': 'form-control input-sm'}
            ),
            'audience': Select(attrs={'class': 'form-control input-sm'}),
            'tags': CheckboxSelectMultiple(),
            'roomresponsible': CheckboxSelectMultiple,
        }
        labels = {
            'custom_name': _('Navn')
        }

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user')
        self.instance = kwargs.get('instance')

        unit = None
        if self.instance is not None:
            unit = self.instance.organizationalunit
        if unit is None and \
                self.user is not None and self.user.userprofile is not None:
            unit = self.user.userprofile.organizationalunit

        self.current_unit = unit

        if not self.instance.pk and 'initial' in kwargs:
            kwargs['initial']['tilbudsansvarlig'] = self.user.pk
            if unit is not None:
                kwargs['initial']['organizationalunit'] = unit.pk

        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['organizationalunit'].queryset = self.get_unit_query_set()
        self.fields['type'].widget = HiddenInput()

        if unit is not None and 'locality' in self.fields:
            self.fields['locality'].choices = [BLANK_OPTION] + \
                [
                    (x.id, x.name_and_address)
                    for x in Locality.objects.order_by(
                        # Sort stuff where unit is null last
                        OrderBy(Q(organizationalunit__isnull=False),
                                descending=True),
                        # Sort localities belong to current unit first
                        OrderBy(Q(organizationalunit=unit), descending=True),
                        # Lastly, sort by name
                        "name"
                    )
                ]

        if 'duration' in self.fields:
            self.fields['duration'].choices = [
                ('00:00', _(u'Ingen')), ('00:15', _(u'15 minutter')),
                ('00:30', _(u'30 minutter')), ('00:45', _(u'45 minutter')),
                ('01:00', _(u'1 time')), ('01:15', _(u'1 time, 15 minutter')),
                ('01:30', _(u'1 time, 30 minutter')),
                ('01:45', _(u'1 time, 45 minutter')),
                ('02:00', _(u'2 timer')),
                ('02:30', _(u'2 timer, 30 minutter')),
                ('03:00', _(u'3 timer')),
                ('03:30', _(u'3 timer, 30 minutter')),
                ('04:00', _(u'4 timer')),
                ('04:30', _(u'4 timer, 30 minutter')),
                ('05:00', _(u'5 timer')),
                ('05:30', _(u'5 timer, 30 minutter')),
                ('06:00', _(u'6 timer')),
                ('06:30', _(u'6 timer, 30 minutter')),
                ('07:00', _(u'7 timer')),
                ('07:30', _(u'7 timer, 30 minutter')),
                ('08:00', _(u'8 timer')),
                ('08:30', _(u'8 timer, 30 minutter')),
                ('09:00', _(u'9 timer')),
                ('09:30', _(u'9 timer, 30 minutter')),
                ('10:00', _(u'10 timer')), ('11:00', _(u'11 timer')),
                ('12:00', _(u'12 timer')), ('13:00', _(u'13 timer')),
                ('14:00', _(u'14 timer')), ('15:00', _(u'15 timer')),
                ('20:00', _(u'20 timer')), ('24:00', _(u'24 timer')),
                ('36:00', _(u'36 timer')), ('48:00', _(u'48 timer'))
            ]

        if 'tilbudsansvarlig' in self.fields:
            qs = self.fields['tilbudsansvarlig']._get_queryset()
            self.fields['tilbudsansvarlig']._set_queryset(
                qs.filter(userprofile__organizationalunit=unit)
            )
            self.fields['tilbudsansvarlig'].label_from_instance = \
                lambda obj: "%s (%s) <%s>" % (
                    obj.get_full_name(),
                    obj.username,
                    obj.email
                )

        if 'roomresponsible' in self.fields:
            qs = self.fields['roomresponsible']._get_queryset()
            self.fields['roomresponsible']._set_queryset(
                qs.filter(organizationalunit=unit)
            )
            self.fields['roomresponsible'].label_from_instance = \
                lambda obj: "%s <%s>" % (
                    obj.get_full_name(),
                    obj.email
                )

    def clean_type(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.type
        else:
            return self.cleaned_data['type']

    def clean(self):
        cleaned_data = super(ProductForm, self).clean()
        min_visitors = cleaned_data.get('minimum_number_of_visitors')
        max_visitors = cleaned_data.get('maximum_number_of_visitors')
        if min_visitors is not None and max_visitors is not None and \
           min_visitors > max_visitors:
            min_error_msg = _(u"The minimum numbers of visitors " +
                              u"must not be larger than " +
                              u"the maximum number of visitors")
            max_error_msg = _(u"The maximum numbers of visitors " +
                              u"must not be smaller than " +
                              u"the minimum number of visitors")
            self.add_error('minimum_number_of_visitors', min_error_msg)
            self.add_error('maximum_number_of_visitors', max_error_msg)
            raise forms.ValidationError(min_error_msg)

    def get_unit_query_set(self):
        """"Get units for which user can create events."""
        user = self.user
        return user.userprofile.get_unit_queryset()


class StudentForADayForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'state',
                  'institution_level', 'topics', 'audience',
                  'time_mode', 'duration', 'locality',
                  'tilbudsansvarlig', 'organizationalunit',
                  'preparation_time', 'comment',
                  )
        widgets = ProductForm.Meta.widgets


class InternshipForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'state',
                  'institution_level', 'topics', 'audience',
                  'time_mode', 'locality',
                  'tilbudsansvarlig', 'organizationalunit',
                  'preparation_time', 'comment',
                  )
        widgets = ProductForm.Meta.widgets


class OpenHouseForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'state',
                  'institution_level', 'topics', 'audience',
                  'time_mode', 'locality',
                  'tilbudsansvarlig', 'organizationalunit',
                  'preparation_time', 'comment',
                  )
        widgets = ProductForm.Meta.widgets


class TeacherProductForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'price', 'state',
                  'institution_level', 'topics', 'audience',
                  'minimum_number_of_visitors', 'maximum_number_of_visitors',
                  'do_create_waiting_list', 'waiting_list_length',
                  'waiting_list_deadline_days', 'waiting_list_deadline_hours',
                  'time_mode', 'duration', 'locality',
                  'tilbudsansvarlig', 'roomresponsible', 'organizationalunit',
                  'preparation_time', 'comment',
                  )
        widgets = ProductForm.Meta.widgets


class ClassProductForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'price', 'state',
                  'institution_level', 'topics', 'audience',
                  'minimum_number_of_visitors', 'maximum_number_of_visitors',
                  'do_create_waiting_list', 'waiting_list_length',
                  'waiting_list_deadline_days', 'waiting_list_deadline_hours',
                  'time_mode', 'duration', 'locality',
                  'tour_available', 'catering_available',
                  'presentation_available', 'custom_available', 'custom_name',
                  'tilbudsansvarlig', 'roomresponsible', 'organizationalunit',
                  'preparation_time', 'comment',
                  )
        widgets = ProductForm.Meta.widgets
        labels = ProductForm.Meta.labels


class StudyProjectForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'state',
                  'institution_level', 'topics', 'audience',
                  'time_mode', 'locality',
                  'tilbudsansvarlig', 'organizationalunit',
                  'preparation_time', 'comment',
                  )
        widgets = ProductForm.Meta.widgets


class AssignmentHelpForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'state',
                  'institution_level', 'topics', 'audience',
                  'tilbudsansvarlig', 'organizationalunit',
                  'comment',
                  )
        widgets = ProductForm.Meta.widgets


class StudyMaterialForm(ProductForm):
    class Meta:
        model = Product
        fields = ('type', 'title', 'teaser', 'description', 'price', 'state',
                  'institution_level', 'topics', 'audience',
                  'tilbudsansvarlig', 'organizationalunit',
                  'comment'
                  )
        widgets = ProductForm.Meta.widgets


class OtherProductForm(ProductForm):
    class Meta:
        model = Product
        fields = ProductForm.Meta.fields
        widgets = ProductForm.Meta.widgets


ProductStudyMaterialFormBase = inlineformset_factory(Product,
                                                     StudyMaterial,
                                                     fields=('file',),
                                                     can_delete=True, extra=1)


class ProductStudyMaterialForm(ProductStudyMaterialFormBase):

    def __init__(self, data, instance=None):
        super(ProductStudyMaterialForm, self).__init__(data)
        self.studymaterials = StudyMaterial.objects.filter(product=instance)


class ProductAutosendForm(forms.ModelForm):
    class Meta:
        model = ProductAutosend
        fields = ['template_key', 'enabled', 'days']
        widgets = {
            'template_key': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super(ProductAutosendForm, self).__init__(*args, **kwargs)

        template_key = None
        if 'instance' in kwargs:
            template_key = kwargs['instance'].template_key
        elif 'initial' in kwargs:
            template_key = kwargs['initial']['template_key']
        if template_key is not None:
            template_type = EmailTemplateType.get(template_key)
            if not template_type.enable_days:
                self.fields['days'].widget = forms.HiddenInput()
            elif template_key == \
                    EmailTemplateType.NOTITY_ALL__BOOKING_REMINDER:
                self.fields['days'].help_text = _(u'Notifikation vil blive '
                                                  u'afsendt dette antal dage '
                                                  u'før besøget')
            elif template_key == EmailTemplateType.NOTIFY_HOST__HOSTROLE_IDLE:
                self.fields['days'].help_text = _(u'Notifikation vil blive '
                                                  u'afsendt dette antal dage '
                                                  u'efter første booking er '
                                                  u'foretaget')

    def label(self):
        return EmailTemplateType.get_name(self.initial['template_key'])


ProductAutosendFormSetBase = inlineformset_factory(
    Product,
    ProductAutosend,
    form=ProductAutosendForm,
    extra=0,
    max_num=len(EmailTemplateType.key_choices),
    can_delete=False,
    can_order=False
)


class ProductAutosendFormSet(ProductAutosendFormSetBase):
    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            autosends = kwargs['instance'].get_autosends(True)
            if len(autosends) < len(EmailTemplateType.key_choices):
                initial = []
                existing_keys = [
                    autosend.template_key for autosend in autosends
                ]
                for key, label in EmailTemplateType.key_choices:
                    if key not in existing_keys:
                        initial.append({
                            'template_key': key,
                            'enabled': False,
                            'days': ''
                        })
                initial.sort(key=lambda choice: choice['template_key'])
                kwargs['initial'] = initial
                self.extra = len(initial)
        super(ProductAutosendFormSet, self).__init__(*args, **kwargs)


class BookingForm(forms.ModelForm):

    scheduled = False

    eventtime = forms.ChoiceField(
        required=False,
        label=_(u"Tidspunkt"),
        choices=(),
    )

    desired_time = forms.CharField(
        widget=Textarea(attrs={'class': 'form-control input-sm'}),
        required=False
    )

    class Meta:
        model = Booking
        fields = ['eventtime', 'notes']
        labels = {
            'eventtime': _(u"Tidspunkt")
        },
        widgets = {
            'notes': Textarea(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, data=None, product=None, *args, **kwargs):
        super(BookingForm, self).__init__(data, *args, **kwargs)

        self.product = product
        # self.scheduled = visit is not None and \
        #    visit.type == Product.FIXED_SCHEDULE_GROUP_VISIT
        self.scheduled = (
            product is not None and
            product.time_mode != Product.TIME_MODE_GUEST_SUGGESTED
        )
        if self.scheduled:
            choices = []
            qs = product.future_bookable_times.order_by('start', 'end')
            for eventtime in qs:
                date = eventtime.interval_display

                visit = eventtime.visit
                product = eventtime.product

                if visit:
                    available_seats = eventtime.visit.available_seats
                else:
                    available_seats = product.maximum_number_of_visitors

                if available_seats is None:
                    choices.append((eventtime.pk, date))
                elif available_seats > 0 or \
                        visit and visit.waiting_list_capacity > 0:
                    if visit:
                        capacity_text = \
                            _("(%d pladser tilbage, "
                              "%d ventelistepladser tilbage)") % \
                            (available_seats, visit.waiting_list_capacity)
                    else:
                        capacity_text = _("(%d pladser tilbage)") % \
                            available_seats
                    choices.append(
                        (eventtime.pk, "%s %s" % (date, capacity_text))
                    )

            self.fields['eventtime'].choices = choices
            self.fields['eventtime'].required = True
        else:
            self.fields['desired_time'].required = True

        if product is not None and 'subjects' in self.fields and \
                product.institution_level != Subject.SUBJECT_TYPE_BOTH:
            qs = None
            if product.institution_level == Subject.SUBJECT_TYPE_GRUNDSKOLE:
                qs = Subject.grundskolefag_qs()
            elif product.institution_level == Subject.SUBJECT_TYPE_GYMNASIE:
                qs = Subject.gymnasiefag_qs()
            if qs:
                self.fields['subjects'].choices = [
                    (subject.id, subject.name) for subject in qs
                ]

    def save(self, commit=True, *args, **kwargs):
        booking = super(BookingForm, self).save(commit, *args, **kwargs)
        if booking.visit:
            booking.visit.desired_time = self.cleaned_data['desired_time']
        return booking


class BookerForm(forms.ModelForm):

    class Meta:
        model = Guest
        fields = ('firstname', 'lastname', 'email', 'phone', 'line',
                  'level', 'attendee_count')
        widgets = {
            'firstname': TextInput(
                attrs={'class': 'form-control input-sm',
                       'placeholder': _(u'Fornavn')}
            ),
            'lastname': TextInput(
                attrs={'class': 'form-control input-sm',
                       'placeholder': _(u'Efternavn')}
            ),
            'email': EmailInput(
                attrs={'class': 'form-control input-sm',
                       'placeholder': _(u'Email')}
            ),
            'phone': TextInput(
                attrs={'class': 'form-control input-sm',
                       'placeholder': _(u'Telefonnummer'),
                       'pattern': '(\(\+\d+\)|\+\d+)?\s*\d+[ \d]*'},
            ),
            'line': Select(
                attrs={'class': 'selectpicker form-control'}
            ),
            'level': Select(
                attrs={'class': 'selectpicker form-control'}
            ),
            'attendee_count': NumberInput(
                attrs={'class': 'form-control input-sm', 'min': 0}
            ),
        }

    repeatemail = forms.CharField(
        widget=TextInput(
            attrs={'class': 'form-control input-sm',
                   'placeholder': _(u'Gentag email')}
        )
    )
    school = forms.CharField(
        widget=TextInput(
            attrs={'class': 'form-control input-sm',
                   'autocomplete': 'off'}
        )
    )
    postcode = forms.IntegerField(
        widget=NumberInput(
            attrs={'class': 'form-control input-sm',
                   'placeholder': _(u'Postnummer'),
                   'min': '1000', 'max': '9999'}
        ),
        required=False
    )
    city = forms.CharField(
        widget=TextInput(
            attrs={'class': 'form-control input-sm',
                   'placeholder': _(u'By')}
        ),
        required=False
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        widget=Select(
            attrs={'class': 'selectpicker form-control'}
        ),
        required=False
    )

    def __init__(self, data=None, products=[], language='da', *args, **kwargs):
        super(BookerForm, self).__init__(data, *args, **kwargs)
        attendeecount_widget = self.fields['attendee_count'].widget

        attendeecount_widget.attrs['min'] = 1
        if len(products) > 0:
            attendeecount_widget.attrs['min'] = max([1] + [
                product.minimum_number_of_visitors
                for product in products if product.minimum_number_of_visitors
            ])
            attendeecount_widget.attrs['max'] = min([10000] + [
                product.maximum_number_of_visitors
                for product in products if product.maximum_number_of_visitors
            ])

            # union or intersection?
            level = binary_or(*[
                product.institution_level for product in products
            ])

            self.fields['school'].widget.attrs['data-institution-level'] = \
                level
            available_level_choices = Guest.level_map[level]
            self.fields['level'].choices = [(u'', BLANK_LABEL)] + [
                (value, title)
                for (value, title) in Guest.level_choices
                if value in available_level_choices
            ]

            for product in products:
                # Visit types where attendee count is mandatory
                if product.type in [
                    Product.GROUP_VISIT, Product.TEACHER_EVENT,
                    Product.STUDY_PROJECT
                ]:
                    self.fields['attendee_count'].required = True
                # Class level is not mandatory for teacher events.
                if product.type == Product.TEACHER_EVENT:
                    self.fields['level'].required = False

        # Eventually we may want a prettier solution,
        # but for now this will have to do
        if language == 'en':
            self.fields['region'].choices = [
                (
                    region.id,
                    region.name_en
                    if region.name_en is not None else region.name
                )
                for region in Region.objects.all()
            ]

    def clean_postcode(self):
        postcode = self.cleaned_data.get('postcode')
        if postcode is not None:
            try:
                PostCode.objects.get(number=postcode)
            except:
                raise forms.ValidationError(_(u'Ukendt postnummer'))
        return postcode

    def clean(self):
        cleaned_data = super(BookerForm, self).clean()
        email = cleaned_data.get("email")
        repeatemail = cleaned_data.get("repeatemail")
        level = cleaned_data.get("level")

        if level == '':
            cleaned_data['level'] = Guest.other

        if email is not None and repeatemail is not None \
                and email != repeatemail:
            error = forms.ValidationError(
                _(u"Indtast den samme email-adresse i begge felter")
            )
            self.add_error('repeatemail', error)

    def save(self):
        booker = super(BookerForm, self).save(commit=False)
        data = self.cleaned_data
        schoolname = data.get('school')
        try:
            school = School.objects.get(name__iexact=schoolname)
        except:
            school = School()
            school.name = schoolname
            school.postcode = PostCode.objects.get(number=data.get('postcode'))
            school.save()
        booker.school = school
        booker.save()
        return booker


class ClassBookingForm(BookingForm):

    class Meta:
        model = ClassBooking
        fields = ('tour_desired', 'catering_desired', 'presentation_desired',
                  'custom_desired', 'eventtime', 'notes')
        labels = BookingForm.Meta.labels
        widgets = BookingForm.Meta.widgets

    def __init__(self, data=None, product=None, *args, **kwargs):
        super(ClassBookingForm, self).__init__(data, product, *args, **kwargs)

        if self.product is not None:
            for service in ['tour', 'catering', 'presentation', 'custom']:
                if not getattr(self.product, service + '_available'):
                    del self.fields[service + '_desired']

    def save(self, commit=True, *args, **kwargs):
        booking = super(ClassBookingForm, self).save(commit=False)
        data = self.cleaned_data

        for service in ['tour_desired', 'catering_desired',
                        'presentation_desired', 'custom_desired']:
            if service not in data:
                data[service] = False
                setattr(booking, service, False)

        if commit:
            booking.save(*args, **kwargs)
        return booking


class TeacherBookingForm(BookingForm):
    class Meta:
        model = TeacherBooking
        fields = ('subjects', 'notes', 'eventtime')
        labels = BookingForm.Meta.labels
        widgets = BookingForm.Meta.widgets


class StudentForADayBookingForm(BookingForm):
    class Meta:
        model = Booking
        fields = ('notes', 'eventtime')
        labels = BookingForm.Meta.labels
        widgets = BookingForm.Meta.widgets


class StudyProjectBookingForm(BookingForm):
    class Meta:
        model = Booking
        fields = ('notes', 'eventtime')
        labels = BookingForm.Meta.labels
        widgets = BookingForm.Meta.widgets


class BookingSubjectLevelFormBase(forms.ModelForm):
    class Meta:
        fields = ('subject', 'level')
        widgets = {
            'subject': Select(
                attrs={'class': 'form-control'}
            ),
            'level': Select(
                attrs={'class': 'form-control'}
            )
        }

    def get_queryset(self):
        return Subject.objects.all()

    def __init__(self, *args, **kwargs):
        super(BookingSubjectLevelFormBase, self).__init__(*args, **kwargs)
        # 16338: Put in a different name for each choice
        self.fields['subject'].choices = [
            (item.id, item.name) for item in self.get_queryset()
        ]


class BookingGymnasieSubjectLevelFormBase(BookingSubjectLevelFormBase):
    class Meta:
        model = BookingGymnasieSubjectLevel
        fields = BookingSubjectLevelFormBase.Meta.fields
        widgets = BookingSubjectLevelFormBase.Meta.widgets

    def get_queryset(self):
        return Subject.gymnasiefag_qs()


class BookingGrundskoleSubjectLevelFormBase(BookingSubjectLevelFormBase):
    class Meta:
        model = BookingGrundskoleSubjectLevel
        fields = BookingSubjectLevelFormBase.Meta.fields
        widgets = BookingSubjectLevelFormBase.Meta.widgets

    def get_queryset(self):
        return Subject.grundskolefag_qs()


BookingGymnasieSubjectLevelForm = \
    inlineformset_factory(
        ClassBooking,
        BookingGymnasieSubjectLevel,
        form=BookingGymnasieSubjectLevelFormBase,
        can_delete=True,
        extra=1,
    )


BookingGrundskoleSubjectLevelForm = \
    inlineformset_factory(
        ClassBooking,
        BookingGrundskoleSubjectLevel,
        form=BookingGrundskoleSubjectLevelFormBase,
        can_delete=True,
        extra=1,
    )


class EmailTemplateForm(forms.ModelForm):

    class Meta:
        model = EmailTemplate
        fields = ('key', 'subject', 'body', 'organizationalunit')
        widgets = {
            'subject': TextInput(attrs={'class': 'form-control'}),
            'body': Textarea(attrs={'rows': 10, 'cols': 90}),
            # 'body': TinyMCE(attrs={'rows': 10, 'cols': 90}),
        }

    def __init__(self, user, *args, **kwargs):
        super(EmailTemplateForm, self).__init__(*args, **kwargs)
        self.fields['organizationalunit'].choices = [BLANK_OPTION] + [
            (x.pk, unicode(x))
            for x in user.userprofile.get_unit_queryset()]


class EmailTemplatePreviewContextEntryForm(forms.Form):
    key = forms.CharField(
        max_length=256,
        widget=TextInput(attrs={'class': 'form-control emailtemplate-key'})
    )
    type = forms.ChoiceField(
        choices=(
            ('string', _(u'Tekst')),
            ('OrganizationalUnit', _(u'Enhed')),
            ('Product', _(u'Tilbud')),
            ('Visit', _(u'Besøg')),
            # ('StudyMaterial', StudyMaterial),
            # ('Product',Product),
            # ('Subject', Subject),
            # ('GymnasieLevel', GymnasieLevel),
            # ('Room', Room),
            # ('PostCode', PostCode),
            # ('School', School),
            ('Booking', _(u'Tilmelding')),
        ),
        widget=Select(attrs={'class': 'form-control emailtemplate-type'})
    )
    value = forms.CharField(
        max_length=1024,
        widget=TextInput(
            attrs={
                'class': 'form-control emailtemplate-value '
                         'emailtemplate-type-string'
            }
        )
    )

EmailTemplatePreviewContextForm = formset_factory(
    EmailTemplatePreviewContextEntryForm
)


class BaseEmailComposeForm(forms.Form):
    required_css_class = 'required'

    body = forms.CharField(
        max_length=65584,
        # widget=TinyMCE(attrs={'rows': 10, 'cols': 90}),
        widget=Textarea(attrs={'rows': 10, 'cols': 90}),
        label=_(u'Tekst')
    )


class EmailComposeForm(BaseEmailComposeForm):

    recipients = ExtensibleMultipleChoiceField(
        label=_(u'Modtagere'),
        widget=CheckboxSelectMultiple
    )

    subject = forms.CharField(
        max_length=77,
        label=_(u'Emne'),
        widget=TextInput(attrs={
            'class': 'form-control'
        })
    )


class GuestEmailComposeForm(BaseEmailComposeForm):

    name = forms.CharField(
        max_length=100,
        label=_(u'Navn'),
        widget=TextInput(
            attrs={
                'class': 'form-control input-sm',
                'placeholder': _(u'Dit navn')
            }
        )
    )

    email = forms.EmailField(
        label=_(u'Email'),
        widget=EmailInput(
            attrs={
                'class': 'form-control input-sm',
                'placeholder': _(u'Din email-adresse')
            }
        )
    )

    phone = forms.CharField(
        label=_(u'Telefon'),
        widget=TextInput(
            attrs={
                'class': 'form-control input-sm',
                'placeholder': _(u'Dit telefonnummer'),
                'pattern': '(\(\+\d+\)|\+\d+)?\s*\d+[ \d]*'
            },
        ),
        required=False
    )


class EmailReplyForm(forms.Form):
    reply = forms.CharField(
        label=_(u'Mit svar'),
        widget=Textarea(attrs={'class': 'form-control input-sm'}),
        required=True
    )


class BookingListForm(forms.Form):
    bookings = forms.MultipleChoiceField(
        widget=CheckboxSelectMultiple()
    )


class AcceptBookingForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea,
        label=_(u'Kommentar'),
        required=False
    )


class EvaluationOverviewForm(forms.Form):
    user = None

    organizationalunit = forms.MultipleChoiceField(
        label=_(u'Afgræns ud fra enhed(er)'),
        required=False,
    )

    limit_to_personal = forms.BooleanField(
        label=_(u'Begræns til besøg jeg personligt er involveret i'),
        required=False
    )

    def __init__(self, qdict, *args, **kwargs):
        self.user = kwargs.pop("user")
        userprofile = self.user.userprofile

        super(EvaluationOverviewForm, self).__init__(qdict, *args, **kwargs)

        self.fields['organizationalunit'].choices = [
            (x.pk, unicode(x)) for x in userprofile.get_unit_queryset()
        ]


class MultiProductVisitTempDateForm(forms.ModelForm):
    class Meta:
        model = MultiProductVisitTemp
        fields = ['date']
        widgets = {
            'date': DateInput(
                attrs={'class': 'datepicker form-control'}
            )
        }
        labels = {
            'date': _(u'Vælg dato')
        }

    def __init__(self, *args, **kwargs):
        super(MultiProductVisitTempDateForm, self).__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%d-%m-%Y', '%d.%m.%Y']


class MultiProductVisitTempProductsForm(forms.ModelForm):
    class Meta:
        model = MultiProductVisitTemp
        fields = ['products', 'required_visits', 'notes']
        widgets = {
            'products': OrderedMultipleHiddenChooser(),
            'notes': Textarea(
                attrs={'class': 'form-control input-sm'}
            )
        }

    def clean_products(self):
        products = self.cleaned_data['products']
        common_institution = binary_and([
            product.institution_level for product in products
        ])
        if common_institution == 0:
            raise forms.ValidationError(
                _(u"Nogle af de valgte tilbud henvender sig kun til "
                  u"folkeskoleklasser, og andre kun til gymnasieklasser"),
                code='conflict'
            )
        return products

    def clean(self):
        super(MultiProductVisitTempProductsForm, self).clean()
        if 'products' not in self.cleaned_data or \
                len(self.cleaned_data['products']) == 0:
            raise forms.ValidationError(
                _(u"Der er ikke valgt nogen produkter")
            )
        products_selected = 0 if 'products' not in self.cleaned_data \
            else len(self.cleaned_data['products'])
        if self.cleaned_data['required_visits'] > products_selected:
            self.cleaned_data['required_visits'] = products_selected
