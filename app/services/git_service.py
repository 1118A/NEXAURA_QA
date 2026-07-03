import shutil
import logging
from pathlib import Path
from git import Repo
from git.exc import GitCommandError

from app.config import REPOS_DIR
from app.exceptions import RepositoryError

logger = logging.getLogger(__name__)

class GitService:
    @staticmethod
    def get_repo_name(repo_url: str) -> str:
        repo_url = repo_url.strip()
        if not repo_url:
            raise RepositoryError("Repository URL is empty.", code="EMPTY_URL")
        
        name = repo_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
            
        if not name:
            raise RepositoryError("Could not detect repository name from URL.", code="INVALID_URL")
            
        return name

    def clone_or_update_repo(self, repo_url: str) -> Path:
        REPOS_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            repo_name = self.get_repo_name(repo_url)
        except RepositoryError:
            raise
        except Exception as e:
            raise RepositoryError(f"Invalid URL format: {str(e)}", code="INVALID_URL")
            
        repo_path = REPOS_DIR / repo_name
        
        # If directory already exists
        if repo_path.exists():
            if (repo_path / ".git").exists():
                try:
                    logger.info(f"Repository {repo_name} exists. Pulling latest updates...")
                    repo = Repo(repo_path)
                    repo.remotes.origin.pull()
                    return repo_path
                except Exception as e:
                    logger.warning(f"Git pull failed for {repo_name}: {str(e)}. Re-cloning...")
                    try:
                        shutil.rmtree(repo_path)
                    except Exception as rm_err:
                        raise RepositoryError(
                            f"Failed to clear existing directory {repo_path}: {str(rm_err)}",
                            code="CLONE_FAILURE"
                        )
            else:
                try:
                    shutil.rmtree(repo_path)
                except Exception as rm_err:
                    raise RepositoryError(
                        f"Failed to clear non-git directory at {repo_path}: {str(rm_err)}",
                        code="CLONE_FAILURE"
                    )

        # Clone repository
        logger.info(f"Cloning repository {repo_url} into {repo_path}...")
        try:
            Repo.clone_from(repo_url, repo_path)
            logger.info(f"Cloned successfully: {repo_name}")
            return repo_path
        except GitCommandError as e:
            err_msg = str(e)
            logger.error(f"Git Command Error: {err_msg}")
            
            if "Authorization Required" in err_msg or "Authentication failed" in err_msg or "Permission denied" in err_msg:
                raise RepositoryError(
                    "Access denied. The repository may be private or requires authentication.",
                    code="PRIVATE_REPO_DENIED"
                )
            elif "not found" in err_msg or "Could not resolve host" in err_msg:
                raise RepositoryError(
                    "Repository not found. Please verify the URL is correct and public.",
                    code="INVALID_URL"
                )
            else:
                raise RepositoryError(
                    f"Git clone command failed: {err_msg}",
                    code="CLONE_FAILURE"
                )
        except Exception as e:
            logger.error(f"Unexpected git clone exception: {str(e)}")
            raise RepositoryError(f"Failed to clone repository: {str(e)}", code="CLONE_FAILURE")

    def delete_repo(self, repo_url: str) -> None:
        try:
            repo_name = self.get_repo_name(repo_url)
            repo_path = REPOS_DIR / repo_name
            if repo_path.exists():
                shutil.rmtree(repo_path)
                logger.info(f"Deleted repository directory {repo_path}")
        except Exception as e:
            logger.error(f"Error deleting repository {repo_url}: {str(e)}")
