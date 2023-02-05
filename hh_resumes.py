import requests
from hh_oauth import sign_in_hh
from google_sheets import get_resume_ids


def get_resume(access_token, resume_id):
    url = f'https://api.hh.ru/resumes/{resume_id}'
    headers={'Authorization': f'Bearer {access_token}'}
    params={
        'with_job_search_status': True
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()


def main():
    resume_ids = get_resume_ids()
    with sign_in_hh() as access_token:   
        for resume_id in resume_ids:
            found_resume = get_resume(access_token, resume_id['id'])
            if found_resume:
                job_search_status = found_resume['job_search_status']['name']
                print(f'Резюме: {resume_id["name"]} - {job_search_status}')


if __name__ == '__main__':
    main()