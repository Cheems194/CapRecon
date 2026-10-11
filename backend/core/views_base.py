from rest_framework.views import APIView
from rest_framework.exceptions import ParseError, NotFound
from core.models import Organization


class TenantScopedAPIView(APIView):
    #Base view that enforces organization isolation via the X-Organization header

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        org_slug = request.headers.get('X-Organization')
        if not org_slug:
            raise ParseError({"error": "Missing X-Organization header."})

        try:
            request.tenant = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise NotFound({"error": f"Organization '{org_slug}' not found."})
