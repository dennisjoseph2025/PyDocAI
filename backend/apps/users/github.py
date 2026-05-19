import requests
from django.conf import settings


def exchange_code_for_token(code: str) -> str | None:
    resp = requests.post(
        'https://github.com/login/oauth/access_token',
        data={
            'client_id':     settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code':          code,
        },
        headers={'Accept': 'application/json'},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get('access_token')


def get_github_user(access_token: str) -> dict:
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept':        'application/vnd.github+json',
    }
    profile = requests.get(
        'https://api.github.com/user',
        headers=headers,
        timeout=10,
    )
    profile.raise_for_status()
    data = profile.json()

    # GitHub users can hide their email — fall back to the emails endpoint
    if not data.get('email'):
        emails_resp = requests.get(
            'https://api.github.com/user/emails',
            headers=headers,
            timeout=10,
        )
        emails_resp.raise_for_status()
        primary = next(
            (e['email'] for e in emails_resp.json() if e['primary'] and e['verified']),
            None,
        )
        data['email'] = primary

    return data