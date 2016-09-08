# encoding: utf-8
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import UpdateView, FormView
from booking.resource_based.forms import ResourceTypeForm, EditItemResourceForm
from booking.resource_based.forms import EditVehicleResourceForm
from booking.resource_based.models import ResourceType, Resource
from booking.resource_based.models import ItemResource, RoomResource
from booking.resource_based.models import TeacherResource, VehicleResource
from booking.views import BackMixin
from itertools import chain

import booking.models as booking_models


class ResourceCreateView(BackMixin, FormView):
    template_name = "resource/typeform.html"
    form_class = ResourceTypeForm
    just_preserve_back = True

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        context = {'form': form}
        context.update(kwargs)
        if form.is_valid():
            typeId = int(form.cleaned_data['type'])
            unitId = int(form.cleaned_data['unit'])

            return self.redirect(reverse(
                'resource-create-type',
                kwargs={'type': typeId, 'unit': unitId}
            ))

        return self.render_to_response(
            self.get_context_data(**context)
        )


class ResourceDetailView(TemplateView):

    template_name = "resource/details.html"

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs['pk']
        self.object = None
        try:
            self.object = Resource.get_subclass_instance(pk)
        except Resource.DoesNotExist:
            raise Http404
        return super(ResourceDetailView, self).dispatch(
            request, *args, **kwargs
        )

    def get_context_data(self, **kwargs):
        context = {
            'object': self.object
        }
        context.update(kwargs)
        return super(ResourceDetailView, self).get_context_data(**context)


class ResourceListView(ListView):
    model = Resource
    template_name = "resource/list.html"

    def get_context_object_name(self, queryset):
        return "resources"

    def get_queryset(self):
        return chain(
            ItemResource.objects.all(),
            RoomResource.objects.all(),
            TeacherResource.objects.all(),
            VehicleResource.objects.all()
        )


class ResourceUpdateView(BackMixin, UpdateView):
    template_name = "resource/form.html"
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.set_object(kwargs.get("pk"), request)
        return super(ResourceUpdateView, self).dispatch(
            request, *args, **kwargs
        )

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            self.get_context_data(form=self.get_form())
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            if 'unit' in self.kwargs:
                unitId = int(self.kwargs['unit'])
                self.object = form.save(commit=False)
                self.object.organizationalunit = \
                    booking_models.OrganizationalUnit.objects.get(id=unitId)
                self.object.save()
            else:
                self.object = form.save(commit=True)
        return self.redirect(reverse('resource-view', args=[self.object.id]))

    def get_form_class(self):
        if 'type' in self.kwargs:
            type = int(self.kwargs['type'])
        else:
            type = self.object.resource_type.id
        if type == ResourceType.RESOURCE_TYPE_ITEM:
            form_class = EditItemResourceForm
        elif type == ResourceType.RESOURCE_TYPE_VEHICLE:
            form_class = EditVehicleResourceForm
        return form_class

    def get_context_data(self, **kwargs):
        context = {}
        context['object'] = self.object
        context.update(kwargs)
        return super(ResourceUpdateView, self).get_context_data(**context)

    def set_object(self, pk, request, is_cloning=False):
        if is_cloning or not hasattr(self, 'object') or self.object is None:
            if pk is None:
                try:
                    typeId = int(self.kwargs['type'])
                    self.object = Resource.create_subclass_instance(typeId)
                except Exception as e:
                    print e
                    pass
            else:
                try:
                    self.object = Resource.get_subclass_instance(pk)
                    if is_cloning:
                        self.object.pk = None
                        self.object.id = None
                except Resource.DoesNotExist:
                    raise Http404

        if self.object.pk:
            self.is_creating = False
        else:
            self.is_creating = True
            self.object.created_by = self.request.user
