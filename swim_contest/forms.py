from django.forms import modelformset_factory

from .models import Result

ResultFormSet = modelformset_factory(
    Result,
    fields=('race_number', 'path_number', 'result_time'),
    extra=0,
    can_delete=False,
)
