import shutil
from pathlib import Path
from git import Repo

from app.config import REPOS_DIR


def get_repo_name(repo_url: str) -> str:
    name = repo_url.rstrip("/").split("/")[-1]

    if name.endswith(".git"):
        name = name[:-4]

    return name


def clone_or_update_repo(repo_url: str) -> Path:
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    repo_name = get_repo_name(repo_url)
    repo_path = REPOS_DIR / repo_name

    if repo_path.exists():
        repo = Repo(repo_path)
        repo.remotes.origin.pull()
        return repo_path

    Repo.clone_from(repo_url, repo_path)
    return repo_path


def delete_repo(repo_url: str) -> None:
    repo_name = get_repo_name(repo_url)
    repo_path = REPOS_DIR / repo_name

    if repo_path.exists():
        shutil.rmtree(repo_path)