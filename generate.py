# coding: utf-8

"""Generate github-actions dashboard."""

import argparse
import os
from urllib.parse import urlparse

from github import Auth, Github
import jinja2


class GithubUrlParsing:
    """Extract information from Github url."""

    def __init__(self, repo_full_name, github_base_url="https://github.com"):
        """Initialize GithubUrlParsing class.

        :param str repo_full_name:
            Github user/organization + repo name, example: python/mypy
        :param str github_base_url:
            Default Github url to used, can be a Github Enterprise url
        """
        self.github_repo_url = github_base_url + "/" + repo_full_name

    def get_workflow_url(self):
        """Get Github-Actions workflow url.

        :return str github_workflow_url:
            The fully Github-Action url

        >>> t = GithubUrlParsing(repo_full_name="python/mypy")
        >>> t.get_workflow_url()
        'https://github.com/python/mypy/actions'
        """
        return self.github_repo_url + "/actions"

    def get_badge_url(self, workflow_filename):
        """Get github badge url for the given repository.

        :param str workflow_filename:
            The Github-Action workflow filename (e.g. ci.yml).

        :return str github_badge_url_status:
            The fully Github-Action badge status url.

        >>> t = GithubUrlParsing(repo_full_name="python/mypy")
        >>> t.get_badge_url(workflow_filename="main.yml")
        'https://github.com/python/mypy/actions/workflows/main.yml/badge.svg'

        >>> t.get_badge_url(workflow_filename="run_mypy_primer.yml")
        'https://github.com/python/mypy/actions/workflows/run_mypy_primer.yml/badge.svg'
        """
        return (
            self.github_repo_url
            + "/actions/workflows/"
            + workflow_filename
            + "/badge.svg"
        )

    def get_markdown_badge_url(self, workflow_name, workflow_filename):
        """Get Github badge url in markdown format.

        :param str workflow_name:
            The Github-Action workflow display name.
        :param str workflow_filename:
            The Github-Action workflow filename (e.g. ci.yml).

        :return str github_badge_url_status:
            The fully Github-Action badge status url in markdown format.

        >>> t = GithubUrlParsing(repo_full_name="python/mypy")
        >>> t.get_markdown_badge_url(workflow_name="main", workflow_filename="main.yml")
        '[![main](https://github.com/python/mypy/actions/workflows/main.yml/badge.svg)](https://github.com/python/mypy/actions)'

        >>> t.get_markdown_badge_url(workflow_name="Run mypy_primer", workflow_filename="run_mypy_primer.yml")
        '[![Run mypy_primer](https://github.com/python/mypy/actions/workflows/run_mypy_primer.yml/badge.svg)](https://github.com/python/mypy/actions)'
        """
        return (
            "[!["
            + workflow_name
            + "]("
            + self.get_badge_url(workflow_filename)
            + ")]("
            + self.get_workflow_url()
            + ")"
        )


def generate_file(template_file, template_vars, template_dir_path="templates") -> None:
    """Generate file from jinja2 template file

    :param str template_file:
        Jinja2 template input file.
    :param dict template_vars:
        Jinja2 template input variables.
    :param str template_dir_path:
        Jinja2 template input folder path.
    """
    jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir_path))
    jinja_template = jinja_env.get_template(template_file)
    jinja_render = jinja_template.render(template_vars)

    file_dest = template_file.replace(".j2", "")
    with open(file_dest, "w") as _file:
        _file.write(jinja_render)


def parsing_agrv():
    """Parsing script arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--github-api-url",
        help="Github api base url, example: https://github.my-company.com/api/v3",
        default="https://api.github.com",
        type=str,
        metavar="",
    )
    return parser.parse_args()


def get_all_actions_badges(client) -> list[map]:
    """Get all Github-Actions badge in markdown format

    :param str client:
        Login client to used to authenticate to Github Endpoint API.

    :return list[map] github_workflows:
        Return all Github-Actions markdown badge like this:
        [
            {
                "repo_name": "github-actions-dashboard",
                "markdown_badge_urls": "[![daily](https://github.com/diodonfrost/github-actions-dashboard/workflows/daily/badge.svg)](https://github.com/diodonfrost/github-actions-dashboard)"
            },
            {
                "repo_name": "ansible-role-ohmyzsh",
                "markdown_badge_urls": "[![Ansible Galaxy](https://img.shields.io/badge/galaxy-diodonfrost.ohmyzsh-660198.svg)](https://galaxy.ansible.com/diodonfrost/ohmyzsh)"
            }
        ]
    """
    github_workflows = []
    for repo_info in client.get_user().get_repos():
        workflow_map = {"repo_name": repo_info.name, "markdown_badge_urls": []}
        github_base_url = "https://" + urlparse(repo_info.git_url).hostname

        parse = GithubUrlParsing(
            repo_full_name=repo_info.full_name, github_base_url=github_base_url
        )
        for workflow in repo_info.get_workflows():
            workflow_filename = os.path.basename(workflow.path)
            markdown_badge = parse.get_markdown_badge_url(
                workflow_name=workflow.name, workflow_filename=workflow_filename
            )
            workflow_map["markdown_badge_urls"].append(markdown_badge)

        if workflow_map["markdown_badge_urls"]:
            github_workflows.append(workflow_map)
    return github_workflows


def main():
    """Main entrypoint function."""
    github_api_url = parsing_agrv().github_api_url
    client = Github(base_url=github_api_url, auth=Auth.Token(os.getenv("GITHUB_TOKEN")))

    github_workflows_badges = get_all_actions_badges(client=client)

    generate_file(
        template_file="README.md.j2",
        template_vars={"github_workflows": github_workflows_badges},
    )


if __name__ == "__main__":
    main()
