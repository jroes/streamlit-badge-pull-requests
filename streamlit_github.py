"""Special utility functions to use PyGithub with Streamlit."""

import streamlit as st
import functools
import math
import time
import re
from datetime import datetime
from github import Github
from github import NamedUser
from github import ContentFile
from github import Repository
from github import RateLimitExceededException
from github import GithubException
from github import MainClass as GithubMainClass

def _get_attr_func(attr):
    """Returns a function which gets this attribute from an object."""

    def get_attr_func(obj):
        return getattr(obj, attr)
    return get_attr_func

# This dictionary of hash functions allows you to safely intermix PyGithub
# with Streamit caching.
GITHUB_HASH_FUNCS = {
    GithubMainClass.Github: lambda _: None,
    NamedUser.NamedUser: _get_attr_func('login'),
    ContentFile.ContentFile: _get_attr_func('download_url'),
    Repository.Repository: _get_attr_func('git_url'),
}

def rate_limit(func):
    """Function decorator to try to handle Github search rate limits.
    See: https://developer.github.com/v3/search/#rate-limit"""

    @functools.wraps(func)
    def wrapped_func(github, *args, **kwargs):
        try:
            return func(github, *args, **kwargs)
        except RateLimitExceededException:
            # We were rate limited by Github, Figure out how long to wait.
            # Round up, and wait that long.
            MAX_WAIT_SECONDS = 60.0
            search_limit = github.get_rate_limit().search
            remaining = search_limit.reset - datetime.utcnow()
            wait_seconds = math.ceil(remaining.total_seconds() + 1.0)
            wait_seconds = min(wait_seconds, MAX_WAIT_SECONDS)
            with st.spinner(f'Waiting {wait_seconds}s to avoid rate limit.'):
                time.sleep(wait_seconds)
            return func(github, *args, **kwargs)
    return wrapped_func

# The URL of the app badge to include in the apps README.md
BADGE_URL = r"https://static.streamlit.io/badges/streamlit_badge_black_white.svg"

class GithubCoords:
    """The path of a Github file, consisting of owner, repo, branch, and path."""

    def __init__(self, owner: str, repo: str, branch: str, path: str) -> None:
        """Constructor."""

        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.path = path

    @staticmethod
    def from_app_url(url: str) -> 'GithubCoords':
        """Returns the GithubCoords given a Streamlit url."""

        # Parse the Stremalit URL into component parts
        streamlit_app_url = re.compile(
            r"https://share.streamlit.io/"
            r"(?P<owner>[\w-]+)/"
            r"(?P<repo>[\w-]+)/"
            r"(?P<branch>[\w-]+)/"
            r"(?P<path>[\w-]+\.py)"
        )
        matched_url = streamlit_app_url.match(url)
        return GithubCoords(
            matched_url.group('owner'),
            matched_url.group('repo'),
            matched_url.group('branch'),
            matched_url.group('path')
        )

    @staticmethod
    def from_github_url(url: str) -> 'GithubCoords':
        """Returns the GithubCoords given a Github url."""

        # Parse the Github URL into component parts
        github_url = re.compile(
             r"https://github.com/"
             r"(?P<owner>[\w-]+)/"
             r"(?P<repo>[\w-]+)/blob/"
             r"(?P<branch>[\w-]+)/"
             r"(?P<path>[\w-]+\.md)"
             )
        matched_url = github_url.match(url)
        return GithubCoords(
            matched_url.group('owner'),
            matched_url.group('repo'),
            matched_url.group('branch'),
            matched_url.group('path')
        )

@rate_limit
@st.cache(hash_funcs=GITHUB_HASH_FUNCS)
def from_access_token(access_token):
    """Returns a ghitub object from an access token."""

    github = Github(access_token) 
    return github

@rate_limit
@st.cache(hash_funcs=GITHUB_HASH_FUNCS, persist=True)
def get_user_from_email(github, email):
    """Returns a user for that email or None."""

    users = list(github.search_users(f'type:user {email} in:email'))
    if len(users) == 0:
        return None
    elif len(users) == 1:
        return users[0]
    else:
        raise RuntimeError(f'{email} associated with {len(users)} users.')

@rate_limit
@st.cache(hash_funcs=GITHUB_HASH_FUNCS, persist=True)
def get_streamlit_files(github, github_login):
    """Returns every single file on github which imports streamlit."""

    try:
        SEARCH_QUERY = 'extension:py "import streamlit as st" user:'
        files = github.search_code(SEARCH_QUERY + github_login)
        return list(files)
    except RateLimitExceededException:
        raise
    except GithubException as e:
        if e.data['message'] == 'Validation Failed':
            # Then this user changed their permissions, I think.
            # In any case, we just pretend they have no files.
            return []
        else:
            # In this case, we have no idea what's going on, so just raise again. 
            raise

@st.cache(hash_funcs=GITHUB_HASH_FUNCS)
def get_repo(github: GithubMainClass.Github, coords: GithubCoords) -> Repository.Repository:
    """Get a live reference to the repository pointed
    by these Github coordinates."""

    return github.get_repo(f"{coords.owner}/{coords.repo}")

def get_contents(github: GithubMainClass.Github, coords: GithubCoords) -> ContentFile.ContentFile:
    """Get a live reference to the file contents pointed
    by these Github coordinates."""

    return get_repo(github, coords).get_contents(coords.path, ref=coords.branch)

