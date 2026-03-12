import os

from core.powershell import run_powershell


class HyperVManager:
    def __init__(self, vm_name, switch_name, nat_name, subnet):
        self.vm_name = vm_name
        self.switch_name = switch_name
        self.nat_name = nat_name
        self.subnet = subnet

    def is_hyperv_enabled(self):
        result = run_powershell(
            "(Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V).State"
        )
        return result.ok and "Enabled" in result.stdout

    def get_windows_edition(self):
        result = run_powershell(
            "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').EditionID"
        )
        return result.stdout.strip() if result.ok else ""

    def is_home_edition(self):
        edition = self.get_windows_edition().lower()
        return edition in {"core", "coren", "corecountryspecific", "coreSingleLanguage".lower()}

    def is_hyperv_management_available(self):
        result = run_powershell(
            "if (Get-Command Get-VM -ErrorAction SilentlyContinue) { 'yes' } else { 'no' }"
        )
        return result.ok and result.stdout == "yes"

    def can_force_enable_on_home(self):
        packages_dir = os.path.join(
            os.environ.get("SystemRoot", r"C:\Windows"),
            "servicing",
            "Packages",
        )
        if not os.path.isdir(packages_dir):
            return False
        try:
            return any("Hyper-V" in name and name.endswith(".mum") for name in os.listdir(packages_dir))
        except OSError:
            return False

    def vm_exists(self):
        result = run_powershell(
            f"if (Get-VM -Name '{self.vm_name}' -ErrorAction SilentlyContinue) {{ 'yes' }} else {{ 'no' }}"
        )
        return result.ok and result.stdout == "yes"

    def ensure_switch(self):
        command = (
            f"$switch = Get-VMSwitch -Name '{self.switch_name}' -ErrorAction SilentlyContinue; "
            f"if (-not $switch) {{ New-VMSwitch -SwitchName '{self.switch_name}' -SwitchType Internal | Out-Null }}"
        )
        return run_powershell(command, timeout=60).ok

    def ensure_nat(self, gateway_ip):
        prefix = f"{gateway_ip}/{self.subnet.split('/')[1]}"
        command = (
            f"$adapter = Get-NetAdapter | Where-Object {{$_.Name -Like '*{self.switch_name}*'}} | Select-Object -First 1; "
            f"if ($adapter) {{ "
            f"$ip = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
            f"Where-Object {{$_.IPAddress -eq '{gateway_ip}'}}; "
            f"if (-not $ip) {{ New-NetIPAddress -IPAddress '{gateway_ip}' -PrefixLength {self.subnet.split('/')[1]} "
            f"-InterfaceIndex $adapter.ifIndex | Out-Null }} "
            f"}}; "
            f"if (-not (Get-NetNat -Name '{self.nat_name}' -ErrorAction SilentlyContinue)) {{ "
            f"New-NetNat -Name '{self.nat_name}' -InternalIPInterfaceAddressPrefix '{prefix}' | Out-Null }}"
        )
        return run_powershell(command, timeout=60).ok

    def create_vm(self, vm_dir, base_vhdx):
        os.makedirs(vm_dir, exist_ok=True)
        vm_vhdx = os.path.join(vm_dir, f"{self.vm_name}.vhdx")
        command = (
            f"if (-not (Test-Path '{vm_vhdx}')) {{ Copy-Item -Path '{base_vhdx}' -Destination '{vm_vhdx}' -Force }}; "
            f"if (-not (Get-VM -Name '{self.vm_name}' -ErrorAction SilentlyContinue)) {{ "
            f"New-VM -Name '{self.vm_name}' -MemoryStartupBytes 4GB -Generation 2 -VHDPath '{vm_vhdx}' "
            f"-SwitchName '{self.switch_name}' | Out-Null; "
            f"Set-VMProcessor -VMName '{self.vm_name}' -Count 2 | Out-Null; "
            f"Set-VMFirmware -VMName '{self.vm_name}' -EnableSecureBoot Off | Out-Null }}"
        )
        return run_powershell(command, timeout=180).ok, vm_vhdx

    def get_vm_mac_address(self):
        result = run_powershell(
            f"(Get-VMNetworkAdapter -VMName '{self.vm_name}' | Select-Object -First 1 -ExpandProperty MacAddress)"
        )
        return result.stdout.strip() if result.ok else ""

    def attach_seed_disk(self, seed_disk_path):
        command = (
            f"$existing = Get-VMHardDiskDrive -VMName '{self.vm_name}' -ErrorAction SilentlyContinue | "
            f"Where-Object {{$_.Path -eq '{seed_disk_path}'}}; "
            f"if (-not $existing) {{ Add-VMHardDiskDrive -VMName '{self.vm_name}' -Path '{seed_disk_path}' | Out-Null }}"
        )
        return run_powershell(command, timeout=60).ok

    def start_vm(self):
        return run_powershell(
            f"$vm = Get-VM -Name '{self.vm_name}' -ErrorAction SilentlyContinue; "
            f"if ($vm -and $vm.State -ne 'Running') {{ Start-VM -Name '{self.vm_name}' | Out-Null }}",
            timeout=60,
        ).ok

    def stop_vm(self):
        return run_powershell(
            f"Stop-VM -Name '{self.vm_name}' -Force -TurnOff",
            timeout=60,
        ).ok

    def remove_vm(self):
        return run_powershell(
            f"if (Get-VM -Name '{self.vm_name}' -ErrorAction SilentlyContinue) "
            f"{{ Stop-VM -Name '{self.vm_name}' -Force -TurnOff -ErrorAction SilentlyContinue; "
            f"Remove-VM -Name '{self.vm_name}' -Force }}",
            timeout=120,
        ).ok

    def create_seed_disk(self, seed_disk_path, source_dir):
        os.makedirs(os.path.dirname(seed_disk_path), exist_ok=True)
        command = (
            f"$path = '{seed_disk_path}'; "
            f"$source = '{source_dir}'; "
            f"if (Test-Path $path) {{ Remove-Item $path -Force }}; "
            f"New-VHD -Path $path -Dynamic -SizeBytes 64MB | Out-Null; "
            f"$disk = Mount-VHD -Path $path -Passthru; "
            f"Initialize-Disk -Number $disk.DiskNumber -PartitionStyle MBR | Out-Null; "
            f"$partition = New-Partition -DiskNumber $disk.DiskNumber -UseMaximumSize -AssignDriveLetter; "
            f"Format-Volume -Partition $partition -FileSystem FAT32 -NewFileSystemLabel 'CIDATA' -Confirm:$false | Out-Null; "
            f"$driveLetter = ($partition | Get-Volume).DriveLetter; "
            f"Copy-Item -Path (Join-Path $source '*') -Destination ($driveLetter + ':\\') -Recurse -Force; "
            f"Dismount-VHD -Path $path"
        )
        return run_powershell(command, timeout=180).ok

    def ensure_portproxy(self, listen_port, connect_address, connect_port):
        command = (
            f"netsh interface portproxy delete v4tov4 listenport={listen_port} listenaddress=127.0.0.1 | Out-Null; "
            f"netsh interface portproxy add v4tov4 listenport={listen_port} listenaddress=127.0.0.1 "
            f"connectport={connect_port} connectaddress={connect_address}"
        )
        return run_powershell(command, timeout=60).ok
