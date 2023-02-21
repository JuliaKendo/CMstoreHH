import redis
import requests

from contextlib import suppress

from hh_oauth import sign_in_hh
from exceptions import handle_errors, HhTokenError, NoEmployeeData


def get_resume(access_token, resume_id):
    url = f'https://api.hh.ru/resumes/{resume_id}'
    headers={'Authorization': f'Bearer {access_token}'}
    params={
        'with_job_search_status': True
    }

    with suppress(requests.exceptions.HTTPError):
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()
    
    if response.status_code != 404:
        raise HhTokenError


def update_job_search_status(redis_conn, resume_id, job_search_status):
    redis_conn.hmset(resume_id, job_search_status)


def get_job_search_status(redis_conn, resume_id):
    job_search_status = redis_conn.hmget(resume_id, 'id')[0]
    if job_search_status:
        return job_search_status.decode()


@handle_errors()
@sign_in_hh()
def get_job_search_statuses(resume_ids, redis_serv, access_token=''):
    job_statuses, employees_with_unavailable_statuses = [], []

    redis_conn =  redis.from_url(f'redis://{redis_serv}/0')
    for resume_id in resume_ids:
        found_resume = get_resume(access_token, resume_id['id'])
        if not found_resume:
            continue
        current_job_search_status = found_resume['job_search_status']
        saved_job_search_status = get_job_search_status(redis_conn, resume_id['id'])
        
        if not current_job_search_status:
            employees_with_unavailable_statuses.append(resume_id['name'])
            continue

        if current_job_search_status['id'] == saved_job_search_status:
            continue

        update_job_search_status(redis_conn, resume_id['id'], current_job_search_status)
        if current_job_search_status['id'] == 'active_search':
            job_statuses.append(f'Резюме {resume_id["name"]} изменило статус на активный поиск!')
    
    return job_statuses, employees_with_unavailable_statuses
