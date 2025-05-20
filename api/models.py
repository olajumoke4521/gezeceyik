from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import datetime 
from parler.models import TranslatableModel, TranslatedFields


class Language(models.Model): 
    code = models.CharField(max_length=2, primary_key=True, unique=True)
    name = models.CharField(max_length=50)
    flag_icon_key = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Category(TranslatableModel):
    translations = TranslatedFields(
        name = models.CharField(_("Name"), max_length=255)
    )
    icon_key = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.safe_translation_getter("name", default=f"Category {self.pk}")

    class Meta:
        verbose_name_plural = _("Categories")

class ExpectationDefinition(TranslatableModel): # Inherit from TranslatableModel
    translations = TranslatedFields(
        name = models.CharField(_("Label"), max_length=255)
    )
    key = models.CharField(max_length=50, primary_key=True, unique=True)
    icon_key = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.safe_translation_getter("name", default=f"Expectation {self.key}")

class SortTagDefinition(TranslatableModel):
    translations = TranslatedFields(
        name = models.CharField(_("Label"), max_length=255)
    )
    TYPE_CHOICES = (
        ('general', _('General')),
        ('region', _('Region')),
        ('amenity', _('Amenity')),
    )
    key = models.CharField(max_length=50, primary_key=True, unique=True)
    icon_key = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')

    def __str__(self):
        return self.safe_translation_getter("name", default=f"SortTag {self.key}")

class Place(TranslatableModel):
    translations = TranslatedFields(
        name = models.CharField(_("Name"), max_length=255),
        description = models.TextField(_("Description"), blank=True, null=True)
    )
    category = models.ForeignKey(Category, verbose_name=_("Category"), related_name='places', on_delete=models.CASCADE)

    address = models.CharField(_("Address"), max_length=500, blank=True, null=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=9, decimal_places=6, null=True, blank=True)
    main_image = models.URLField(_("Main Image URL"), max_length=500, blank=True, null=True)
    website = models.URLField(_("Website"), max_length=200, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    whatsapp = models.CharField(_("WhatsApp"), max_length=20, blank=True, null=True)
    map_link = models.URLField(_("Map Link"), max_length=500, blank=True, null=True)

    instagram = models.URLField(_("Instagram"), blank=True, null=True)
    twitter = models.URLField(_("Twitter"), blank=True, null=True)
    facebook = models.URLField(_("Facebook"), blank=True, null=True)
    pinterest = models.URLField(_("Pinterest"), blank=True, null=True)

    # Expectations (Boolean fields)
    outside_area = models.BooleanField(_("Outside Area"), default=False)
    inside_area = models.BooleanField(_("Inside Area"), default=False)
    reservation = models.BooleanField(_("Reservation Taken"), default=False)
    kids_menu = models.BooleanField(_("Kids Menu"), default=False)
    baby_sit = models.BooleanField(_("Baby Sitting"), default=False)
    kard_pay = models.BooleanField(_("Card Payment"), default=False)
    cash = models.BooleanField(_("Cash Payment"), default=False)
    free_park_area = models.BooleanField(_("Free Parking Area"), default=False)
    bar = models.BooleanField(_("Bar"), default=False)
    coffee = models.BooleanField(_("Coffee"), default=False)
    dessert = models.BooleanField(_("Dessert"), default=False)
    kitchen = models.BooleanField(_("Kitchen"), default=False)
    wheelchair_accessible_entrance = models.BooleanField(_("Wheelchair Accessible"), default=False)
    pets_allow = models.BooleanField(_("Pets Allow"), default=False)
    fish = models.BooleanField(_("Fish"), default=False)
    meat_and_chicken = models.BooleanField(_("Meat/Chicken"), default=False)

    # Sorting Tags (Boolean fields)
    popular = models.BooleanField(_("Popular"), default=False)
    historical_places = models.BooleanField(_("Historical Places"), default=False)
    alcohol = models.BooleanField(_("Alcohol"), default=False)
    beach = models.BooleanField(_("Beach"), default=False)
    coffee = models.BooleanField(_("Coffee"), default=False)
    creative_places = models.BooleanField(_("Creative Place"), default=False)
    castles = models.BooleanField(_("Castle"), default=False)
    museum = models.BooleanField(_("Museum"), default=False)
    parks = models.BooleanField(_("Parks"), default=False)
    waterfalls = models.BooleanField(_("Waterfalls"), default=False)
    hiking_trails = models.BooleanField(_("Hiking trails"), default=False)

    # Region Tags (Boolean fields)
    kyrenia = models.BooleanField(_("Kyrenia"), default=False)
    nicosia = models.BooleanField(_("Nicosia"), default=False)
    famagusta = models.BooleanField(_("Famagusta"), default=False)
    iskele = models.BooleanField(_("Iskele"), default=False)
    guzelyurt = models.BooleanField(_("Guzelyurt"), default=False)
    karpaz = models.BooleanField(_("Karpaz"), default=False)
    lefke = models.BooleanField(_("Lefke"), default=False)
    currency_supported = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    liked_by_devices = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = _("Place")
        verbose_name_plural = _("Places")
        ordering = ['-created_at', 'translations__name']

    def __str__(self):
        return self.safe_translation_getter("name", default=f"Place {self.pk}")

    def get_working_hours_status(self): 
        now = datetime.now().time()
        today_weekday = datetime.now().weekday()

        status_texts = {"Closed": _("Closed"), "Open": _("Open")}
        current_status = {
            "is_open_now": False,
            "status_text": str(status_texts["Closed"]), 
            "next_change_time": None
        }

        todays_hours = self.open_times.filter(day_of_week=today_weekday).first()

        if todays_hours:
            open_time = todays_hours.open_time
            close_time = todays_hours.close_time

            if close_time < open_time:
                if now >= open_time or now < close_time:
                    current_status["is_open_now"] = True
                    current_status["status_text"] = str(status_texts["Open"])
                    current_status["next_change_time"] = close_time.strftime("%H:%M")
                elif now < open_time:
                    current_status["status_text"] = _("Opens at %(time)s") % {'time': open_time.strftime("%H:%M")}
                    current_status["next_change_time"] = open_time.strftime("%H:%M")
            else:
                if open_time <= now < close_time:
                    current_status["is_open_now"] = True
                    current_status["status_text"] = str(status_texts["Open"])
                    current_status["next_change_time"] = close_time.strftime("%H:%M")
                elif now < open_time:
                    current_status["status_text"] = _("Opens at %(time)s") % {'time': open_time.strftime("%H:%M")}
                    current_status["next_change_time"] = open_time.strftime("%H:%M")
        return current_status


class PlaceImage(models.Model): 
    place = models.ForeignKey(Place, verbose_name=_("Place"), related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=500)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("Place Image")
        verbose_name_plural = _("Place Images")
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.place.safe_translation_getter('name', default=f'Place {self.place_id}')} (Order: {self.order})"
    
class OpeningHour(models.Model):
    DAYS_OF_WEEK = (
        (0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')),
        (3, _('Thursday')), (4, _('Friday')), (5, _('Saturday')),
        (6, _('Sunday')),
    )
    place = models.ForeignKey(Place, verbose_name=_("Place"), related_name='open_times', on_delete=models.CASCADE)
    day_of_week = models.IntegerField(_("Day of Week"),choices=DAYS_OF_WEEK)
    open_time = models.TimeField(_("Open Time"))
    close_time = models.TimeField(_("Close Time"))

    class Meta:
        verbose_name = _("Opening Hour")
        verbose_name_plural = _("Opening Hours")
        ordering = ['day_of_week', 'open_time']
        unique_together = ('place', 'day_of_week', 'open_time')

    def __str__(self):
        place_name = self.place.safe_translation_getter("name", default=f"Place {self.place_id}")
        return f"{self.get_day_of_week_display()}: {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')} for {place_name}"

