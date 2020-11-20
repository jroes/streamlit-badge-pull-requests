"""A script which lets you batch-add badges to the READMEs of
Streamlit sharing apps."""

import streamlit as st
import streamlit_github
import pandas as pd
from github import MainClass as GithubMainClass
from github.GithubException import UnknownObjectException

# This is where we will store all the forked repositories
FORK_BASE_PATH = 'forks'

def get_config():
    """Returns all the config information to run the app."""

    # Parse and return the information
    access_token = st.sidebar.text_input("Github access token", type="password")
    github = streamlit_github.from_access_token(access_token)
    return github

@st.cache
def get_s4a_apps() -> pd.DataFrame:
    apps = pd.read_csv('sharing_apps_2.csv')
    apps.drop('Unnamed: 0', axis=1, inplace=True)
    return apps

def select_apps() -> pd.DataFrame:
    """Give the user a selection interface with which to select a set
    of apps to process. Displays and returns the selected apps."""

    # Get the app dataframe
    apps = get_s4a_apps()

    # Display the selector
    st.write("## Apps")

    # Let the user select which apps to focus on.
    first_app_index, last_app_index = \
       st.slider("Select apps", 0, len(apps), (0, 1))
    if first_app_index >= last_app_index:
        raise RuntimeError('Must select at least one app.')
    selected_apps = apps[first_app_index:last_app_index].copy()
    st.write(f"Selected `{len(selected_apps)} / {len(apps)}` apps.")
    st.write(selected_apps)

    return selected_apps

def parse_s4a_apps(github: GithubMainClass.Github):
    apps = select_apps()

    # Don't do anything until the use clicks this button.
    if not st.button('Process apps'):
        return

    st.write('## Output')
    has_streamlit_badge = []
    for i, app in enumerate(apps.itertuples()):
        with st.beta_expander(app.app_url):
            st.write(app)
            coords = streamlit_github.GithubCoords.from_app_url(app.app_url)
            st.write('coords', i, coords)
            st.write({attr:getattr(coords, attr)
                for attr in ['owner', 'repo', 'branch', 'path']})
            repo = coords.get_repo(github)
            with st.beta_columns((1, 20))[1]:
                readme = streamlit_github.get_readme(repo)
                readme_contents = readme.decoded_content.decode('utf-8')
                st.text(readme_contents)
            has_badge = streamlit_github.has_streamlit_badge(repo) 
    #        # except (UnknownObjectException, RuntimeError):
    #        except UnknownObjectException:
    #            has_badge = False
    #        except RuntimeError:
    #            has_badge = False
            st.write('has_streamlit_badge', has_badge)
            has_streamlit_badge.append(has_badge)
    apps['has_badge'] = has_streamlit_badge
    st.write("### Processed apps", apps)
    apps.to_csv('out.csv')
    st.success('out.csv')

def main():
    """Execution starts here."""

    # Get a github object from the user's authentication token
    github = get_config()
 
    st.write('Hello, world! Again!!')
    parse_s4a_apps(github)

#     # Test out content_file_from_app_url()
#     app_url = "https://share.streamlit.io/shivampurbia/tweety-sentiment-analyis-streamlit-app/main/Tweety.py"
#     f"**app_url:** `{app_url}`"
#     coords = streamlit_github.GithubCoords.from_app_url(app_url)
#     f"**coords:**", coords
#     content_file = streamlit_github.get_contents(github, coords)
#     st.write(dir(content_file))
#     f"**content_file:**", content_file
#     repo = content_file.repository
#     f"**repo**", repo, repo.git_url
#     st.write(dir(repo))
#     st.code(readme_contents)
#     'has_badge', streamlit_github.BADGE_URL in readme_contents
#     # st.code(content_file.

#     # Test out content_file_from_app_url()
#     github_url = r"https://github.com/tester-burner/test1/blob/main/README.md"
#     f'**github_url** `{github_url}`'
#     coords = streamlit_github.GithubCoords.from_github_url(github_url)
#     content_file = coords.get_contents(github)
#     st.code(content_file.decoded_content.decode('utf-8'), language='markdown')
#     
#     if st.button('Fork the repo'):
#         repo = coords.get_repo(github)
#         'repo', repo
#         streamlit_github.fork_and_clone_repo(repo, FORK_BASE_PATH)


# Start execution at the main() function 
if __name__ == '__main__':
   main()
