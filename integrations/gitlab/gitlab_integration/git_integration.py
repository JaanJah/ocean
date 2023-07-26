from functools import lru_cache
from typing import Dict, Any, Tuple, List

from gitlab_integration.core.entities import FILE_PROPERTY_PREFIX
from gitlab_integration.gitlab_service import GitlabService
from loguru import logger
from pydantic import Field

from port_ocean.context.event import event
from port_ocean.core.handlers import JQEntityProcessor
from port_ocean.core.handlers.port_app_config.models import PortAppConfig


class GitManipulationHandler(JQEntityProcessor):
    @lru_cache()
    def _get_file_content(
        self, gitlab_service: GitlabService, project_id: int, file_path: str, ref: str
    ) -> str:
        return (
            gitlab_service.gitlab_client.projects.get(project_id)
            .files.get(file_path=file_path, ref=ref)
            .decode()
            .decode("utf-8")
        )

    def _validate_project_scope(self, data: Dict[str, Any]) -> Tuple[int, str]:
        if (project_id := data.get("id")) and (ref := data.get("default_branch")):
            return project_id, ref
        raise ValueError("Project id and ref are required")

    def _search(self, data: Dict[str, Any], pattern: str) -> Any:
        if pattern.startswith(FILE_PROPERTY_PREFIX):
            project_id, ref = self._validate_project_scope(data)
            logger.info(
                f"Searching for file {pattern} in Project {project_id}, ref {ref}"
            )
            gitlab_service: GitlabService = event.attributes["project_id_to_service"][
                project_id
            ]

            file_path = pattern.replace(FILE_PROPERTY_PREFIX, "")
            return self._get_file_content(gitlab_service, project_id, file_path, ref)
        else:
            return super()._search(data, pattern)


class GitlabPortAppConfig(PortAppConfig):
    spec_path: str | List[str] = Field(alias="specPath", default="**/port.yml")
    branch: str = "main"