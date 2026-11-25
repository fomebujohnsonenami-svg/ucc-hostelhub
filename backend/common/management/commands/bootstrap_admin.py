from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import LocalCredential, Profile


class Command(BaseCommand):
    help = "Explicitly promote an existing Hostel Hub account to administrator."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--username", required=True)
        parser.add_argument("--promote-existing", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        credential = LocalCredential.objects.select_for_update().filter(email=options["email"].strip().lower()).first()
        if not credential or credential.profile.username != options["username"]:
            raise CommandError("No local account matches that email and username.")
        profile = credential.profile
        if profile.role == Profile.Role.ADMIN:
            self.stdout.write("Administrator already configured.")
            return
        if not options["promote_existing"]:
            raise CommandError("Explicitly authorize the role change with --promote-existing.")
        profile.role = Profile.Role.ADMIN
        profile.save(update_fields=["role", "updated_at"])
        credential.loginsession_set.all().delete()
        self.stdout.write(self.style.SUCCESS("Administrator configured. Sign in again to use the admin dashboard."))
