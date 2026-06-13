import httpx
from typing import Optional
from app.core.config import settings


class GitHubService:
    BASE = "https://api.github.com"

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def trigger_workflow(self, repo: str, workflow_file: str, ref: str = "main",
                               inputs: dict = None) -> Optional[int]:
        """Dispatch a workflow_dispatch event and return the run id."""
        url = f"{self.BASE}/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
        payload = {"ref": ref}
        if inputs:
            payload["inputs"] = inputs

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()

        # GitHub returns 204, run id is found by querying runs right after
        runs = await self.list_runs(repo, workflow_file, ref)
        if runs:
            return runs[0].get("id")
        return None

    async def get_run_status(self, repo: str, run_id: int) -> dict:
        url = f"{self.BASE}/repos/{repo}/actions/runs/{run_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
        return {
            "status": data.get("status"),
            "conclusion": data.get("conclusion"),
            "run_number": data.get("run_number"),
            "html_url": data.get("html_url"),
        }

    async def list_runs(self, repo: str, workflow_file: str, branch: str = "main",
                        per_page: int = 10) -> list:
        url = f"{self.BASE}/repos/{repo}/actions/workflows/{workflow_file}/runs"
        params = {"branch": branch, "per_page": per_page}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("workflow_runs", [])

    async def cancel_run(self, repo: str, run_id: int) -> bool:
        url = f"{self.BASE}/repos/{repo}/actions/runs/{run_id}/cancel"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self.headers)
            return resp.status_code == 202
