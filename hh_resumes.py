import redis
import requests

from contextlib import suppress, contextmanager

from hh_oauth import sign_in_hh
from exceptions import handle_errors, HhTokenError, NoEmployeeData


@contextmanager
def get_redis_conn(redis_serv, db_name='0'):

    conn =  redis.from_url(f'redis://{redis_serv}/{db_name}')
    try:
        yield conn
    finally:
        pass


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
    job_statuses = []

    if not access_token:
        raise HhTokenError

    if not resume_ids:
        raise NoEmployeeData

    with get_redis_conn(redis_serv) as redis_conn:
        for resume_id in resume_ids:
            found_resume = get_resume(access_token, resume_id['id'])
            if not found_resume:
                continue
            current_job_search_status = found_resume['job_search_status']
            saved_job_search_status = get_job_search_status(redis_conn, resume_id['id'])
            
            if current_job_search_status['id'] == saved_job_search_status:
                job_statuses.append(f'Статус резюме: {resume_id["name"]} не изменился')
                continue

            update_job_search_status(redis_conn, resume_id['id'], current_job_search_status)
            job_statuses.append(f'Резюме: {resume_id["name"]} - {current_job_search_status["name"]}')
    
    return job_statuses
