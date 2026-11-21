from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from apps.accounts.models import Profile
from common.supabase_admin import verified_auth_user


class Command(BaseCommand):
    help = "Create or explicitly promote an administrator using a verified Supabase Auth UUID."

    def add_arguments(self, parser):
        parser.add_argument("--auth-id", required=True)
        parser.add_argument("--username", required=True)
        parser.add_argument("--full-name", required=True)
        parser.add_argument("--promote-existing", action="store_true")

    def handle(self, *args, **options):
        user_id = verified_auth_user(options["auth_id"])
        try:
            with transaction.atomic():
                profile = Profile.objects.select_for_update().filter(pk=user_id).first()
                if profile is not None:
                    if profile.username != options["username"]:
                        raise CommandError("The existing profile username did not match.")
                    if profile.role == Profile.Role.ADMIN:
                        self.stdout.write("Administrator already configured.")
                        return
                    if not options["promote_existing"]:
                        raise CommandError("This profile already exists. Explicitly authorize the role change with --promote-existing.")
                    profile.role = Profile.Role.ADMIN
                    profile.save(update_fields=["role", "updated_at"])
                else:
                    profile = Profile(id=user_id, username=options["username"], full_name=options["full_name"], role=Profile.Role.ADMIN)
                    profile.full_clean()
                    profile.save(force_insert=True)
        except (IntegrityError, ValidationError):
            raise CommandError("Could not create the administrator. Verify the username is valid and unused.") from None
        self.stdout.write(self.style.SUCCESS("Administrator configured for the verified Auth account."))
