# encoding: utf-8
from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic.edit import UpdateView, FormMixin, DeleteView, FormView
from booking.resource_based.forms import ResourceTypeForm, EditTeacherResourceForm
from booking.resource_based.models import ResourceType

import booking.models as booking_models


class CreateResourceView(FormView):
    template_name = "resource/typeform.html"
    form_class = ResourceTypeForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        context = {'form': form}
        context.update(kwargs)
        if form.is_valid():
            typeId = int(form.cleaned_data['type'])
            type = ResourceType.objects.get(pk=typeId)
            if typeId == ResourceType.RESOURCE_TYPE_VEHICLE:



            print type.name
            if type.name == ResourceType.default_resource_names[ResourceType.RESOURCE_TYPE_TEACHER]:
                return redirect(
                    reverse('teacher-resource-edit', args={'unit': int(form.cleaned_data['unit'])})
                )
        return self.render_to_response(
            self.get_context_data(**context)
        )

