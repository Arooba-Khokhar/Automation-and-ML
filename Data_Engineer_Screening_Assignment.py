import os
import django
import datetime
from pytz import timezone
from xwing import settings
from gentella.api_access.emarsys.api import EmarsysApi
from collections import namedtuple
from typing import List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xwing.settings")
django.setup()

from gentella.emarsys_models.models import ContactSegment

brand_shop_segment = namedtuple('brand_shop_segment', ['id', 'name', 'count', 'brand'])


def get_segment_info_as_df(brand: str) -> List[brand_shop_segment]:
    assert brand in settings.EMARSYS_LOGINS.keys(), 'passed \'brand\' is not in EMARSYS LOGINS'
    etc_timezone = timezone('Europe/Amsterdam')
    api = EmarsysApi(username=settings.EMARSYS_LOGINS[brand]['username'],
                     secret_token=settings.EMARSYS_LOGINS[brand]['secret'], tzinfo_obj=etc_timezone)
    segment_data = api.get_segments()
    segments = []
    for segment in segment_data:
        segment_count = api.get_segment_contact_count(segment_tuple=segment)
        brand_segment_combo = brand_shop_segment(id=segment_count.id, name=segment_count.name,
                                                 count=segment_count.count, brand=brand)
        segments.append(brand_segment_combo)
    return segments


def save_segments(segment_info: List[brand_shop_segment], brand: str) -> None:
    today = datetime.datetime.today().date()
    ContactSegment.objects.filter(dt=today, brand=brand).delete()
    data_list = []
    for segment in segment_info:
        data = ContactSegment(
            id=segment.id,
            name=segment.name,
            count=segment.count,
            brand=segment.brand,
            dt=today
        )
        data_list.append(data)
    ContactSegment.objects.bulk_create(data_list)


def main() -> None:
    for brand in settings.EMARSYS_LOGINS.keys():
        print(brand)
        segment_list = get_segment_info_as_df(brand=brand)
        save_segments(segment_list, brand=brand)


if __name__ == '__main__':
    main()
