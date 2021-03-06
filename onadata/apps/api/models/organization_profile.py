from django.db import models
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

from onadata.apps.api.models.team import Team
from onadata.apps.main.models import UserProfile


def create_owner_team_and_permissions(sender, instance, created, **kwargs):
    if created:
        team = Team.objects.create(
            name=Team.OWNER_TEAM_NAME, organization=instance.user)
        content_type = ContentType.objects.get(
            app_label='api', model='organizationprofile')
        permission, created = Permission.objects.get_or_create(
            codename="is_org_owner", name="Organization Owner",
            content_type=content_type)
        team.permissions.add(permission)
        instance.creator.groups.add(team)


class OrganizationProfile(UserProfile):
    """Organization: Extends the user profile for organization specific info

        * What does this do?
            - it has a createor
            - it has owner(s), through permissions/group
            - has members, through permissions/group
            - no login access, no password? no registration like a normal user?
            - created by a user who becomes the organization owner
        * What relationships?
    """

    class Meta:
        app_label = 'api'

    is_organization = models.BooleanField(default=True)
    # Other fields here
    creator = models.ForeignKey(User)

    def save(self, *args, **kwargs):
        super(OrganizationProfile, self).save(*args, **kwargs)

    def remove_user_from_organization(self, user):
        """Remove's a user from all teams/groups in the organization
        """
        for group in user.groups.filter('%s#' % self.user.username):
            user.groups.remove(group)

    def is_organization_owner(self, user):
        """Checks if user is in the organization owners team

        :param user: User to check

        :returns: Boolean whether user has organization level permissions
        """
        has_owner_group = user.groups.filter(
            name='%s#%s' % (self.user.username, Team.OWNER_TEAM_NAME))
        return True if has_owner_group else False


post_save.connect(
    create_owner_team_and_permissions, sender=OrganizationProfile,
    dispatch_uid='create_owner_team_and_permissions')
