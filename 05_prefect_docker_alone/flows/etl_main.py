#! /usr/bin/env python3

import httpx
from prefect import flow


@flow(log_prints=True)
def get_repo_info(repo_name: str = "PrefectHQ/prefect"):
    url = f"https://api.github.com/repos/{repo_name}"
    response = httpx.get(url)
    response.raise_for_status()
    repo = response.json()
    print(f"{repo_name} repository statistics 🤓@@🤓@@🤓:")
    print(f"Stars 🌠🌠 : {repo['stargazers_count']}")
    print(f"Forks 🍴 : {repo['forks_count']}")


if __name__ == "__main__":
#     get_repo_info.serve(
#         name="my-first-deployment",
#         cron="* * * * *",
#         tags=["testing", "tutorial"],
#         description="Given a GitHub repository, logs repository statistics for that repo.",
#         version="tutorial/deployments",
#     )

    get_repo_info()
