from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AIStatusView(APIView):
    """
    Check the status and metadata of configured Groq API keys.
    Provider hierarchy: Groq primary -> Groq fallback.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groq_key = getattr(settings, 'GROQ_API_KEY', None)
        groq_key_2 = getattr(settings, 'GROQ_API_KEY_2', None)

        status_data = {
            'providers': {
                'groq_primary': {
                    'configured': bool(groq_key),
                    'status': 'unknown',
                    'role': 'primary',
                    'model': 'llama-3.3-70b-versatile',
                },
                'groq_fallback': {
                    'configured': bool(groq_key_2),
                    'status': 'unknown',
                    'role': 'fallback',
                    'model': 'llama-3.3-70b-versatile',
                },
            },
            'fallback_order': ['groq_primary', 'groq_fallback'],
        }

        # Check primary Groq key
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                client.models.list()
                status_data['providers']['groq_primary']['status'] = 'active'
            except Exception as e:
                status_data['providers']['groq_primary']['status'] = 'invalid'
                status_data['providers']['groq_primary']['error'] = str(e)

        # Check fallback Groq key
        if groq_key_2:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key_2)
                client.models.list()
                status_data['providers']['groq_fallback']['status'] = 'active'
            except Exception as e:
                status_data['providers']['groq_fallback']['status'] = 'invalid'
                status_data['providers']['groq_fallback']['error'] = str(e)

        return Response(status_data)
