from booking.models import Unit
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelChoiceField, EmailField
from django.utils.translation import ugettext_lazy as _
from profile.models import UserRole, UserProfile


class UserCreateForm(UserCreationForm):
    email = EmailField(required=True)
    role = ModelChoiceField(
        required=True,
        queryset=UserRole.objects.all(),
        label=_(u'Rolle')
    )
    unit = ModelChoiceField(
        required=True,
        queryset=Unit.objects.all(),
        label=_(u'Enhed')
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name',
                  'password1', 'password2')

    def __init__(self, *args, **kwargs):
        # pop off the user or the call to super will fail.
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
        # self.fields does not exist until after super is called...
        super(UserCreateForm, self).__init__(*args, **kwargs)

        # Now, we can change the queryset attributes of role and unit fields
        if hasattr(self, 'user'):
            self.fields['role'].queryset = self.get_role_query_set()
            self.fields['unit'].queryset = self.get_unit_query_set()

        if hasattr(self.instance, 'userprofile'):
            self.initial.update({
                'role': self.instance.userprofile.user_role,
                'unit': self.instance.userprofile.unit
            })

    def get_unit_query_set(self):
        """"Get units for which user can create events."""
        return self.user.userprofile.get_unit_queryset()

    def get_role_query_set(self):
        roles = self.user.userprofile.available_roles
        if self.instance == self.user:
            roles.append(self.user.userprofile.get_role())
        qs = UserRole.objects.filter(role__in=roles)
        return qs

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.is_staff = True

        if commit:
            user.save()
        return user


class EditMyResourcesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('my_resources',)
        widgets = {'my_resources': forms.CheckboxSelectMultiple()}
