from djangosaml2.signals import pre_user_save

import booking.models as booking_models
import profile.models as profile_models


def custom_update_user(sender, **kwargs):
    try:
        user = sender

        # Everyone needs access to django-admin
        user.is_staff = True

        attributes = kwargs.pop("attributes", {})

        # Try to look up a unit with the same name as the group provided by
        # SAML.
        group = attributes.pop("http://schemas.xmlsoap.org/claims/Group", None)
        if isinstance(group, list) and len(group) > 0:
            group = group[0]
        else:
            group = None
        if group:
            try:
                group = \
                    booking_models.OrganizationalUnit.objects.get(name=group)
            except booking_models.OrganizationalUnit.DoesNotExist:
                group = None

        # Give the user a profile
        profile = profile_models.UserProfile(
            user=user,
            organizationalunit=group,
            user_role=profile_models.get_none_role()
        )
        profile.save()

        # Create a resource for the user
        if profile.is_teacher and group is not None:
            resource = booking_models.TeacherResource(
                user=user,
                organizationalunit=group
            )
            resource.save()

    except Exception as e:
        print "Error during user autogeneration: %s" % e

    return True

pre_user_save.connect(custom_update_user)
