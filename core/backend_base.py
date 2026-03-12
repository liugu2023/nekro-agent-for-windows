from abc import abstractmethod

from PyQt6.QtCore import QObject, pyqtSignal


class BackendBase(QObject):
    log_received = pyqtSignal(str, str)
    status_changed = pyqtSignal(str)
    boot_finished = pyqtSignal()
    progress_updated = pyqtSignal(str)
    deploy_info_ready = pyqtSignal(dict)

    backend_key = ""
    display_name = ""

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.is_running = False

    @abstractmethod
    def check_environment(self):
        raise NotImplementedError

    @abstractmethod
    def get_default_install_dir(self):
        raise NotImplementedError

    def create_distro(self, install_dir):
        return self.create_runtime(install_dir)

    @abstractmethod
    def create_runtime(self, install_dir):
        raise NotImplementedError

    def prepare_runtime(self):
        return True

    @abstractmethod
    def install_wsl(self):
        raise NotImplementedError

    @abstractmethod
    def install_docker(self):
        raise NotImplementedError

    @abstractmethod
    def start_services(self, deploy_mode):
        raise NotImplementedError

    @abstractmethod
    def stop_services(self):
        raise NotImplementedError

    @abstractmethod
    def update_services(self):
        raise NotImplementedError

    @abstractmethod
    def uninstall_environment(self):
        raise NotImplementedError

    @abstractmethod
    def get_runtime_name(self):
        raise NotImplementedError

    @abstractmethod
    def get_host_access_path(self, guest_path):
        raise NotImplementedError
