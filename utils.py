import streamlit as st
from github import Github, GithubException
import json
import base64

# Secrets에서 설정 불러오기
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]
FILE_PATH = "data/requests.json"

def get_repo():
    """GitHub 리포지토리 객체 반환"""
    g = Github(GITHUB_TOKEN)
    return g.get_repo(REPO_NAME)

def load_data():
    """GitHub에서 JSON 파일을 읽어옴 (없으면 빈 리스트 반환)"""
    repo = get_repo()
    try:
        contents = repo.get_contents(FILE_PATH)
        json_data = base64.b64decode(contents.content).decode('utf-8')
        return json.loads(json_data)
    except GithubException:
        # 파일이 없으면 빈 리스트 반환
        return []

def save_data(new_data_list, commit_message="Update data via Streamlit App"):
    """데이터 리스트를 GitHub JSON 파일에 저장 (Commit)"""
    repo = get_repo()
    json_str = json.dumps(new_data_list, indent=4, ensure_ascii=False)
    
    try:
        # 파일이 이미 있으면 Update
        contents = repo.get_contents(FILE_PATH)
        repo.update_file(
            path=FILE_PATH,
            message=commit_message,
            content=json_str,
            sha=contents.sha
        )
    except GithubException:
        # 파일이 없으면 Create
        repo.create_file(
            path=FILE_PATH,
            message="Initial data creation",
            content=json_str
        )