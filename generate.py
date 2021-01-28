# coding: utf-8

"""Generate github-actions dashboard."""

import os

from github import Github
import jinja2


def generate_markdown_badge(workflow_name, workflow_url, workflow_badge_url) -> str:
    """Generate Github-Actions badge url in markdown format.

    :param str workflow_name:
        Github-Actions workflow name.
    :param str workflow_badge_url:
        Github-Actions badge url.
    :param str workflow_url:
        Github-Actions url.

    return: str markdown_badge_url:
        The fully Github-Actions badge url in markdown format.

    >>> generate_markdown_actions_badge("pytest", "https://github.com/pytest-dev/pytest/workflows/main/badge.svg", "https://github.com/pytest-dev/pytest/actions")
    '[![pytest](https://github.com/pytest-dev/pytest/workflows/main/badge.svg)](https://github.com/pytest-dev/pytest/actions)'
    """
    return (
        "[![" + workflow_name + "](" + workflow_badge_url + ")](" + workflow_url + ")"
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


client = Github(os.getenv("GITHUB_TOKEN"))

github_workflows = []
for repo_info in client.get_user().get_repos():
    workflow_map = {"repo_name": repo_info.name, "markdown_badge_urls": []}

    for workflow in repo_info.get_workflows():
        github_workflow_markdown_badge_url = generate_markdown_badge(
            workflow_name=workflow.name,
            workflow_badge_url=workflow.badge_url,
            workflow_url=repo_info.html_url + "/actions",
        )
        workflow_map["markdown_badge_urls"].append(github_workflow_markdown_badge_url)
    if workflow_map["markdown_badge_urls"]:
        github_workflows.append(workflow_map)

generate_file(
    template_file="README.md.j2", template_vars={"github_workflows": github_workflows}
)
