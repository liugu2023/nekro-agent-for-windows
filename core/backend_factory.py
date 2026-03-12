from core.hyperv_backend import HyperVBackend
from core.wsl_manager import WSLManager


class BackendFactory:
    @staticmethod
    def create(config):
        backend_key = (config.get("backend") or "wsl").lower()

        if backend_key == "hyperv":
            return HyperVBackend(config=config)

        return WSLManager(config=config)
