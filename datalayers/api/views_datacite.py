from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
def datacite(request):
    from datacite import DataCiteRESTClient
    from datacite.errors import DataCiteNotFoundError

    dc = DataCiteRESTClient(None, None, None)
    res = {}
    try:
        datacite = dc.get_metadata(
            request.GET.get("pid", None),
        )
        res["datacite"] = datacite

    except DataCiteNotFoundError:
        res["datacite"] = {}

    return JsonResponse(res)
