from django.shortcuts import render,redirect
import logging
from django.http import JsonResponse
import asana
import hubspot
# from hubspot.crm.deals import SimplePublicObjectInput, ApiException
from pprint import pprint

# from .utils import fetch_task_id, fetch_asana_data  # Assuming these are defined in utils.py

logger = logging.getLogger(__name__)

def asana_auth(request):
    if request.method=='POST':
        try:
            request.session['asana_access_token'] = request.POST['access_token']
            logger.info('Asana access token saved successfully')
            return redirect('sync_asana/')
        except Exception as e:
            logger.error('Error saving Asana access token: ' + str(e))
    logger.info('Asana authentication page loaded')
    return render(request, 'asana_dashboard.html')

def sync_asana(request):
    access_token = request.session.get('asana_access_token')
    if access_token:
        logger.info('Asana asana_workspaces page loaded')
        return render(request, 'asana_workspaces.html')
    else:
        logger.error('Error saving Asana access token: Nt able to Fetch token from Session' )
        return JsonResponse({"error": "Access token not found"}, status=401)
    
def get_workspace(request):
    access_token = request.session.get('asana_access_token')
    
    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    workspaces_api = asana.WorkspacesApi(api_client)

    opts = {
        'limit': 50,
        'opt_fields': "name,is_organization,email_domains"
    }
    workspace_list=[]
    workspaces = workspaces_api.get_workspaces(opts)
    print(workspaces,'------------')
    for i in workspaces:
        workspace_list.append({'gid': i['gid'], 'name': i['name']})
    
    # workspace_list = [w for w in workspaces]
    print(workspace_list)
    return JsonResponse(workspace_list, safe=False)

def get_projects(request):
    access_token = request.session.get('asana_access_token')
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
    access_token = request.session.get('asana_access_token')
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
    
def asanasync(request):
    """
    Fetch task details for a specific section in Asana and create deals in HubSpot.
    """
    # Fetch access tokens from Django session
    hubspot_access_token = request.session.get('hubspot_access_token')
    asana_access_token = request.session.get('access_token')
    section_id = request.GET.get('section_id')
    section_name = request.GET.get('section_name')

    if not asana_access_token:
        return JsonResponse({"error": "Asana access token is missing"}, status=401)
    if not hubspot_access_token:
        return JsonResponse({"error": "HubSpot access token is missing"}, status=401)
    if not section_id or not section_name:
        return JsonResponse({"error": "Section ID or Section Name is missing"}, status=400)

    # Initialize HubSpot client
    client = hubspot.Client.create(access_token=hubspot_access_token)
    synced_deals = []

    # Fetch task IDs for the given Asana section
    try:
        task_ids = fetch_task_id(request,section_id)
        print("Task IDs:", task_ids)
    except Exception as e:
        return JsonResponse({"error": f"Error fetching task IDs: {str(e)}"}, status=500)

    # Iterate over the task IDs and create deals in HubSpot
    for task_id in task_ids:
        try:
            # Fetch data for each task in the section
            data = fetch_asana_data(request,task_id)

            # Prepare properties for HubSpot deal creation
            properties = {
                "dealname": data.get('Deal_name', ''),
                "assignee": data.get('assignee_name', ''),
                "project": data.get('project', ''),
                "section_category": section_name,
                "comment": str(data.get('comment', '')),
                "notes": str(data.get('notes', '')),
            }

            print("Properties for HubSpot Deal:", properties)
            deal_input = SimplePublicObjectInput(properties=properties)

            # Create a deal in HubSpot
            api_response = client.crm.deals.basic_api.create(simple_public_object_input_for_create=deal_input)
            print("Deal created:", api_response)
            synced_deals.append(data['Deal_name'])
        except ApiException as e:
            print(f"Exception when creating deal in HubSpot: {e}")
        except Exception as e:
            print(f"Error fetching or processing task {task_id}: {e}")

    return JsonResponse(synced_deals, safe=False)

def fetch_task_id(request):
    access_token = request.session.get('access_token')
    section_id = request.GET.get('section_id')

    # Check if access token and section ID are available
    if not access_token:
        return JsonResponse({"error": "Asana access token is missing"}, status=401)
    if not section_id:
        return JsonResponse({"error": "Section ID is missing"}, status=400)

    # Initialize Asana API client with the access token
    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    tasks_api_instance = asana.TasksApi(api_client)

    opts = {
        'limit': 50,
        'opt_fields': "name,completed,created_at"
    }

    try:
        # Fetch tasks for the specified section
        tasks = tasks_api_instance.get_tasks_for_section(section_id, opts)
        task_list = [{'gid': task['gid'], 'name': task['name']} for task in tasks]
        return JsonResponse(task_list, safe=False)
    except asana.rest.ApiException as e:
        return JsonResponse({"error": f"Asana API error: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
        
def fetch_task_id(request):
    access_token = request.session.get('access_token')
    section_id = request.GET.get('section_id')

    # Check if access token and section ID are available
    if not access_token:
        return JsonResponse({"error": "Asana access token is missing"}, status=401)
    if not section_id:
        return JsonResponse({"error": "Section ID is missing"}, status=400)

    # Initialize Asana API client with the access token
    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    tasks_api_instance = asana.TasksApi(api_client)

    opts = {
        'limit': 50,
        'opt_fields': "name,completed,created_at"
    }

    try:
        # Fetch tasks for the specified section
        tasks = tasks_api_instance.get_tasks_for_section(section_id, opts)
        task_list = [{'gid': task['gid'], 'name': task['name']} for task in tasks]
        return JsonResponse(task_list, safe=False)
    except asana.rest.ApiException as e:
        return JsonResponse({"error": f"Asana API error: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
    
def fetch_asana_data(request, task_gid):
    """
    Fetch task details and comments from Asana for a specific task.
    """
    # Get access token from Django session
    access_token = request.session.get('access_token')
    if not access_token:
        return JsonResponse({"error": "Asana access token is missing"}, status=401)

    # Initialize Asana API client
    configuration = asana.Configuration()
    configuration.access_token = access_token
    api_client = asana.ApiClient(configuration)
    tasks_api_instance = asana.TasksApi(api_client)
    stories_api_instance = asana.StoriesApi(api_client)

    # Define the fields to fetch for the task
    task_opts = {
        'opt_fields': (
            "actual_time_minutes,approval_status,assignee,assignee.name,"
            "assignee_section,assignee_section.name,completed,completed_at,"
            "created_at,custom_fields,custom_fields.text_value,"
            "memberships,memberships.project,memberships.section,"
            "notes,projects,projects.name"
        )
    }

    try:
        # Fetch task details
        api_response = tasks_api_instance.get_task(task_gid, task_opts)

        # Extract task information
        response = {
            'assignee_name': api_response.get('assignee', {}).get('name', 'Unassigned'),
            'created_at': api_response.get('created_at', ''),
            'Deal_name': api_response.get('name', ''),
            'notes': api_response.get('notes', ''),
            'project': api_response.get('projects', [{}])[0].get('name', ''),
            'section': api_response.get('memberships', [{}])[0].get('section', {}).get('name', '')
        }

        # Fetch comments (stories) for the task
        story_opts = {
            'limit': 50,
            'opt_fields': "created_by.name,text,created_at"
        }
        stories = stories_api_instance.get_stories_for_task(task_gid, story_opts)

        comments = []
        for story in stories:
            try:
                comment = f"{story['created_by']['name']} : {story['text']} ({story['created_at']})"
            except KeyError:
                comment = ''
            comments.append(comment)

        response['comment'] = comments

        return JsonResponse(response, safe=False)

    except ApiException as e:
        error_message = f"Exception when calling Asana API: {str(e)}"
        return JsonResponse({"error": error_message}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)
 
