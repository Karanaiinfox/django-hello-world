from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
import asana
from .models import Contact, Deal
from django.conf import settings


# from asana import ApiException

HUBSPOT_CLIENT_ID = '3fd82bfc-3e0a-4707-bb7c-6e4d5995d989'
HUBSPOT_CLIENT_SECRET = '028b7d9e-6a60-4a8d-8cdd-62c3aad573c9'
HUBSPOT_REDIRECT_URI = 'http://localhost:8000/callback'


def login(request):
    hubspot_auth_url = (
        f"https://app.hubspot.com/oauth/authorize?client_id={HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={HUBSPOT_REDIRECT_URI}&scope=crm.objects.contacts.write%20"
        "crm.schemas.contacts.write%20oauth%20crm.schemas.contacts.read%20"
        "crm.objects.contacts.read"
    )
    return redirect(hubspot_auth_url)


def callback(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({"error": "Authorization failed: No code provided"}, status=400)

    token_url = 'https://api.hubapi.com/oauth/v1/token'
    data = {
        'grant_type': 'authorization_code',
        'client_id': HUBSPOT_CLIENT_ID,
        'client_secret': HUBSPOT_CLIENT_SECRET,
        'redirect_uri': HUBSPOT_REDIRECT_URI,
        'code': code
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        request.session['hubspot_access_token'] = tokens['access_token']
        return redirect('/')
    else:
        return JsonResponse({"error": response.json()}, status=response.status_code)


def index(request):
    return render(request, 'index.html')


def get_workspace(request):
    access_token = request.session.get('access_token')
    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    workspaces_api = asana.WorkspacesApi(api_client)

    opts = {
        'limit': 50,
        'opt_fields': "name,is_organization,email_domains"
    }

    workspaces = workspaces_api.get_workspaces(opts)
    workspace_list = [{'gid': w['gid'], 'name': w['name']} for w in workspaces]
    return JsonResponse(workspace_list, safe=False)


def asana_dashboard(request):
    return render(request, 'asana_dashboard.html')


def sync_asana(request):
    access_token = request.session.get('access_token')
    if access_token:
        return render(request, 'asana_workspaces.html')
    else:
        return JsonResponse({"error": "Access token not found"}, status=401)

def get_projects(request):
    access_token = request.session.get('access_token')
    workspace_gid = request.GET.get('workspace_gid')

    if not access_token:
        return JsonResponse({"error": "Access token is missing"}, status=401)

    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    projects_api_instance = asana.ProjectsApi(api_client)

    opts = {
        'limit': 50,
        'workspace': workspace_gid,
        'archived': False,
        'opt_fields': "name,created_at,modified_at"
    }

    try:
        projects = projects_api_instance.get_projects(opts)
        project_list = [{'gid': project['gid'], 'name': project['name']} for project in projects]
        return JsonResponse(project_list, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_sections(request):
    access_token = request.session.get('access_token')
    project_gid = request.GET.get('project_gid')

    if not access_token:
        return JsonResponse({"error": "Asana access token is missing"}, status=401)

    if not project_gid:
        return JsonResponse({"error": "Project GID is missing"}, status=400)

    # Initialize Asana API client with the access token
    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    sections_api_instance = asana.SectionsApi(api_client)

    # Set optional fields and limit for retrieving sections
    opts = {
        'limit': 50,
        'opt_fields': "name,created_at"
    }

    try:
        # Fetch sections for the specified project
        sections = sections_api_instance.get_sections_for_project(project_gid, opts)
        section_list = [{'gid': section['gid'], 'name': section['name']} for section in sections]
        return JsonResponse(section_list, safe=False)
    except asana.rest.ApiException as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)

