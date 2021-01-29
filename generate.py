# coding: utf-8

"""Generate github-actions dashboard."""

import argparse
import os
from urllib.parse import urlparse

from github import Github
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

    def get_badge_url(self, workflow_name):
        """Get github badge url for the given repository.

        :param str workflow_name:
            The Github-Action workflow name.

        :return str github_badge_url_status:
            The fully Github-Action badge status url.

        >>> t = GithubUrlParsing(repo_full_name="python/mypy")
        >>> t.get_badge_url(workflow_name="main")
        'https://github.com/python/mypy/workflows/main/badge.svg'

        >>> t.get_badge_url(workflow_name="Run mypy_primer")
        'https://github.com/python/mypy/workflows/Run%20mypy_primer/badge.svg'
        """
        return (
            self.github_repo_url
            + "/workflows/"
            + workflow_name.replace(" ", "%20")
            + "/badge.svg"
        )

    def get_markdown_badge_url(self, workflow_name):
        """Get Github badge url in markdown format.

        :param str workflow_name:
            The Github-Action workflow name.

        :return str github_badge_url_status:
            The fully Github-Action badge status url in markdown format.

        >>> t = GithubUrlParsing(repo_full_name="python/mypy")
        >>> t.get_markdown_badge_url(workflow_name="main")
        '[![main](https://github.com/python/mypy/workflows/main/badge.svg)](https://github.com/python/mypy/actions)'

        >>> t.get_markdown_badge_url(workflow_name="Run mypy_primer")
        '[![Run mypy_primer](https://github.com/python/mypy/workflows/Run%20mypy_primer/badge.svg)](https://github.com/python/mypy/actions)'
        """
        return (
            "[!["
            + workflow_name
            + "]("
            + self.get_badge_url(workflow_name)
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


def main():
    """Main entrypoint function."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--github-api-url",
        help="Github api base url, example: https://github.my-company.com/api/v3",
        default="https://api.github.com",
        type=str,
        metavar="",
    )
    args = parser.parse_args()
    github_api_url = args.github_api_url
    client = Github(base_url=github_api_url, login_or_token=os.getenv("GITHUB_TOKEN"))

    github_workflows = []
    for repo_info in client.get_user().get_repos():
        workflow_map = {"repo_name": repo_info.name, "markdown_badge_urls": []}
        github_base_url = "https://" + urlparse(repo_info.git_url).hostname

        for workflow in repo_info.get_workflows():
            parse = GithubUrlParsing(
                repo_full_name=repo_info.full_name, github_base_url=github_base_url
            )
            markdown_badge = parse.get_markdown_badge_url(workflow_name=workflow.name)
            workflow_map["markdown_badge_urls"].append(markdown_badge)

        if workflow_map["markdown_badge_urls"]:
            github_workflows.append(workflow_map)

    generate_file(
        template_file="README.md.j2",
        template_vars={"github_workflows": github_workflows},
    )


if __name__ == "__main__":
    main()
