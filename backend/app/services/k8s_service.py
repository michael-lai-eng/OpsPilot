from typing import Optional
from app.core.config import settings


class K8sService:
    """Kubernetes operations wrapper. Uses official kubernetes-python client."""

    def __init__(self, cluster: str = "default"):
        self.cluster = cluster
        self._client = None

    def _get_client(self):
        from kubernetes import client, config as k8s_config
        if settings.K8S_IN_CLUSTER:
            k8s_config.load_incluster_config()
        elif settings.K8S_KUBECONFIG:
            k8s_config.load_kube_config(config_file=settings.K8S_KUBECONFIG)
        else:
            k8s_config.load_kube_config()
        return client

    async def get_deployment(self, namespace: str, name: str) -> Optional[dict]:
        try:
            k8s = self._get_client()
            apps = k8s.AppsV1Api()
            dep = apps.read_namespaced_deployment(name, namespace)
            return {
                "name": dep.metadata.name,
                "replicas": dep.spec.replicas,
                "ready_replicas": dep.status.ready_replicas or 0,
                "image": dep.spec.template.spec.containers[0].image,
            }
        except Exception:
            return None

    async def update_image(self, namespace: str, name: str, image: str) -> bool:
        try:
            k8s = self._get_client()
            apps = k8s.AppsV1Api()
            patch = {"spec": {"template": {"spec": {"containers": [{"name": name, "image": image}]}}}}
            apps.patch_namespaced_deployment(name, namespace, patch)
            return True
        except Exception as e:
            raise RuntimeError(f"K8s update_image failed: {e}")

    async def scale(self, namespace: str, name: str, replicas: int) -> bool:
        try:
            k8s = self._get_client()
            apps = k8s.AppsV1Api()
            patch = {"spec": {"replicas": replicas}}
            apps.patch_namespaced_deployment_scale(name, namespace, patch)
            return True
        except Exception as e:
            raise RuntimeError(f"K8s scale failed: {e}")

    async def rollout_restart(self, namespace: str, name: str) -> bool:
        from datetime import datetime
        try:
            k8s = self._get_client()
            apps = k8s.AppsV1Api()
            patch = {"spec": {"template": {"metadata": {
                "annotations": {"kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()}
            }}}}
            apps.patch_namespaced_deployment(name, namespace, patch)
            return True
        except Exception as e:
            raise RuntimeError(f"K8s rollout restart failed: {e}")

    async def list_pods(self, namespace: str, label_selector: str = "") -> list:
        try:
            k8s = self._get_client()
            core = k8s.CoreV1Api()
            pods = core.list_namespaced_pod(namespace, label_selector=label_selector)
            return [{"name": p.metadata.name, "phase": p.status.phase,
                     "node": p.spec.node_name, "ip": p.status.pod_ip} for p in pods.items]
        except Exception:
            return []
