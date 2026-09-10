from __future__ import annotations

import hashlib
import importlib.util
import posixpath
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "artifacts/tools/bader_lnx_64.tar.gz"
HELPER = ROOT / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
spec = importlib.util.spec_from_file_location("ssh_ncw", HELPER)
ssh_ncw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(ssh_ncw)

TOOLS = (
    "sfs/CoOH/cp2k/Al16/oer/spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818/tools"
)


def run(client, command: str) -> str:
    _, stdout, stderr = client.exec_command(f"cd {ssh_ncw.REMOTE_ROOT} && {command}")
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode(errors="replace")
    error = stderr.read().decode(errors="replace")
    if code:
        raise RuntimeError(error or output)
    return output


def main() -> None:
    if ARCHIVE.stat().st_size < 1_000_000:
        raise RuntimeError("local Bader archive is unexpectedly small")
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()

    paramiko = ssh_ncw.ensure_paramiko()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ssh_ncw.HOST,
        port=ssh_ncw.PORT,
        username=ssh_ncw.USER,
        password=ssh_ncw.load_password(),
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = client.open_sftp()
        remote_archive = posixpath.join(ssh_ncw.REMOTE_ROOT, TOOLS, "bader_lnx_64.tar.gz")
        sftp.put(str(ARCHIVE), remote_archive)
        output = run(
            client,
            f"cd {TOOLS} && mkdir -p bader-bin && tar -xzf bader_lnx_64.tar.gz -C bader-bin "
            "&& bader-bin/bader -v",
        )
        manifest = (
            "tool\tversion\tsource\tsha256\tscope\n"
            f"bader\t1.05\thttps://github.com/henkelmangroup/bader/releases/latest/"
            f"download/bader_lnx_64.tar.gz\t{digest}\tproject_local_only\n"
        )
        with sftp.open(posixpath.join(ssh_ncw.REMOTE_ROOT, TOOLS, "tool_manifest.tsv"), "w") as handle:
            handle.write(manifest)
        print(output.strip())
        print(digest)
    finally:
        client.close()


if __name__ == "__main__":
    main()
