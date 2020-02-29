from Panacea.models import *
from django.utils.translation import ugettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class custom_user(AbstractUser):
    # User authentication from tut located here:https://wsvincent.com/django-custom-user-model-tutorial/
    username = None
    email = models.EmailField(_('email address'), unique=True)  # changes email to unique and blank to false
    random_field = models.CharField(max_length=80, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', ]

    def __str__(self):
        return self.email


class ReportType(models.Model):
    def __str__(self):
        return self.name

    REPORT_FREQUENCY = (
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Yearly', 'Yearly'),
        ('Other', 'Other')
    )

    name = models.CharField(max_length=100)
    report_frequency = models.CharField(max_length=50,
                                        choices=REPORT_FREQUENCY,
                                        default='Yearly')
    due_date = models.DateField()
    report_owner = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)


class summary_organization_type(models.Model):
    ORGANIZATION_TYPES = (
        ("Community provider", "Community provider"),
        ("Ferry", "Ferry"),
        ("Intercity bus", "Intercity bus"),
        ("Medicaid broker", "Medicaid broker"),
        ("Monorail", "Monorail"),
        ("Transit", "Transit"),
        ("Tribe", "Tribe"),
    )

    name = models.CharField(max_length=120, choices=ORGANIZATION_TYPES)

    def __str__(self):
        return self.name


class organization(models.Model):
    AGENCY_CLASSIFICATIONS = (
        ("Urban", "Urban"),
        ("Small Urban", "Small Urban"),
        ("Rural", "Rural"),
    )
    # TODO move to table
    SUMMARY_ORG_CLASSIFICATIONS = (
        ("Community provider", "Community provider"),
        ("Ferry", "Ferry"),
        ("Intercity bus", "Intercity bus"),
        ("Medicaid broker", "Medicaid broker"),
        ("Monorail", "Monorail"),
        ("Transit", "Transit"),
        ("Tribe", "Tribe"),
    )

    def __str__(self):
        return self.name

    name = models.CharField(max_length=80, blank=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    classification = models.CharField(max_length=50, choices=AGENCY_CLASSIFICATIONS, blank=True, null=True)
    vanpool_program = models.BooleanField(blank=True, null=True, default=True)
    vanshare_program = models.BooleanField(blank=True, null=True)
    vanpool_expansion = models.BooleanField(blank=True, null=True)
    # TODO add to agency profile form
    in_jblm_area = models.BooleanField(blank=True, null=True)  # TODO confirm this is no longer needed
    in_puget_sound_area = models.BooleanField(blank=True, null=True)
    summary_reporter = models.BooleanField(default=True)
    summary_organization_classifications = models.ForeignKey(summary_organization_type, on_delete=models.PROTECT, blank=True, null=True)
    #fixed_route_expansion = models.BooleanField(blank=True, null=True)


class vanpool_details(models.Model):
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name="+")
    vanpool_program_start_date = models.DateField(blank=True, null=True)
    vanpool_program_end_date = models.DateField(blank=True, null= True)


class profile(models.Model):
    custom_user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    profile_submitted = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)
    telephone_number = PhoneNumberField(blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    reports_on = models.ManyToManyField(ReportType, blank=True)  # TODO rename this to something else
    requested_permissions = models.ManyToManyField(Group, blank=True)
    active_permissions_request = models.BooleanField(blank=True, null=True)

@receiver(post_save, sender=custom_user)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile.objects.create(custom_user=instance)


@receiver(post_save, sender=custom_user)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()