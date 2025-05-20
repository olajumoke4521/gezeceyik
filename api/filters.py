import django_filters
from django.db.models import Q
from .models import Place, Category

class PlaceFilter(django_filters.FilterSet):

    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    category_name = django_filters.CharFilter(method='filter_by_category_translated_name')

    expectations = django_filters.CharFilter(method='filter_by_expectations',
                                             label="Filter by comma-separated expectation keys")

    sorting_tags = django_filters.CharFilter(method='filter_by_sorting_tags',
                                             label="Filter by comma-separated sorting/region keys")

    class Meta:
        model = Place
        fields = ['category']

    def filter_by_category_translated_name(self, queryset, name, value):

        if not value:
            return queryset


        return queryset.filter(category__translations__name__icontains=value).distinct()

    def filter_by_expectations(self, queryset, name, value):

        keys = [key.strip() for key in value.split(',') if key.strip()]
        if not keys:
            return queryset
        exp_map = {
            "outsideArea": "outside_area", "kardPay": "kard_pay", "coffee": "coffee",
            "meatAndChicken": "meat_and_chicken",
            "insideArea": "inside_area", "reservation": "reservation", "kidsMenu": "kids_menu", "babySit": "baby_sit",
            "cash": "cash", "freeParkArea": "free_park_area", "bar": "bar", "dessert": "dessert", "kitchen": "kitchen",
            "WheelchairAccessibleEntrance": "wheelchair_accessible_entrance", "petsAllow": "pets_allow", "fish": "fish"
        }

        q_objects = Q()
        for key in keys:
            model_field = exp_map.get(key)
            if model_field:
                q_objects &= Q(**{model_field: True})
            else:
                pass

        return queryset.filter(q_objects)

    def filter_by_sorting_tags(self, queryset, name, value):

        keys = [key.strip() for key in value.split(',') if key.strip()]
        if not keys:
            return queryset

        sort_map = {
            "historicalPlaces": "historical_places", "creativePlaces": "creative_places",
            "hikingTrails": "hiking_trails", "popular": "popular", "alcohol": "alcohol", "beach": "beach",
            "castles": "castles",
            "museum": "museum", "parks": "parks", "waterfalls": "waterfalls",
            "kyrenia": "kyrenia", "nicosia": "nicosia", "famagusta": "famagusta",
            "iskele": "iskele", "guzelyurt": "guzelyurt", "karpaz": "karpaz", "lefke": "lefke"
        }

        q_objects = Q()
        for key in keys:
            model_field = sort_map.get(key)
            if model_field:
                q_objects &= Q(**{model_field: True})
            else:
                pass

        return queryset.filter(q_objects)