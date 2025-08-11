import docker
import time
import subprocess
from pathlib import Path
from os import getcwd

client = docker.from_env()
image = "ubuntu:22.04"
network_name = "ansible-net"

# Get number of worker nodes from user
num_nodes = int(input("Enter the number of worker nodes to create: "))

# Create container name dictionary
container_names = {"ansible-machine": "server"}
for i in range(1, num_nodes + 1):
    container_names[f"node{i}"] = "node"

# Create Docker network if it doesn't exist
try:
    client.networks.get(network_name)
except docker.errors.NotFound:
    client.networks.create(network_name, driver="bridge")

# Remove old containers if any
for name in container_names:
    try:
        client.containers.get(name).remove(force=True)
    except docker.errors.NotFound:
        pass

# Start containers
containers = {}
for name in container_names:
    containers[name] = client.containers.run(
        image,
        name=name,
        tty=True,
        stdin_open=True,
        detach=True,
        privileged=True,
        hostname=name,
        network=network_name,
        command="/bin/bash"
    )

print("⏳ Waiting for containers to initialize...")
time.sleep(10)

# Shared SSH setup commands
ssh_setup = [
    "apt-get update -y -qq",
    "bash -c 'DEBIAN_FRONTEND=noninteractive apt-get install -y -qq sudo openssh-server net-tools vim iputils-ping > /dev/null 2>&1'",
    "ssh-keygen -A",
    "mkdir -p /var/run/sshd",
    "bash -c \"[ -f /etc/ssh/sshd_config ] && sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config || echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config\"",
    "bash -c 'getent passwd ansible || useradd -m -s /bin/bash ansible'",
    "bash -c \"echo 'ansible:ansible' | chpasswd\"",
    "bash -c \"grep -qxF 'ansible ALL=(ALL) NOPASSWD:ALL' /etc/sudoers || echo 'ansible ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers\"",
    "mkdir -p /home/ansible/.ssh",
    "chown -R ansible:ansible /home/ansible/.ssh",
    "chmod 700 /home/ansible/.ssh",
    "bash -c 'test -f /home/ansible/.ssh/authorized_keys && chmod 600 /home/ansible/.ssh/authorized_keys || true'",
    "bash -c 'command -v sshd && nohup /usr/sbin/sshd -D &'"
]

# Extra packages for the control server
server_extra = [
    "bash -c 'DEBIAN_FRONTEND=noninteractive apt-get install -y -qq software-properties-common > /dev/null 2>&1'",
    "bash -c \"add-apt-repository --yes --update ppa:ansible/ansible > /dev/null 2>&1\"",
    "apt-get update -y -qq",
    "bash -c 'DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ansible sshpass > /dev/null 2>&1'",
    "su - ansible -c 'ssh-keygen -q -t rsa -N \"\" -f ~/.ssh/id_rsa'"
]

def run_commands(container, name, commands):
    for cmd in commands:
        print(f"[{name}] $ {cmd}")
        exit_code, output = container.exec_run(cmd, user="root")
        if exit_code != 0:
            print(f"❌ Error ({exit_code}):\n{output.decode()}")
        else:
            print("✅ Done:\n" + output.decode().strip())

# Setup all containers
for name, role in container_names.items():
    run_commands(containers[name], name, ssh_setup)
    if role == "server":
        run_commands(containers[name], name, server_extra)

# Public key injection
print("\n🔑 Injecting public key...")
exit_code, pubkey = containers["ansible-machine"].exec_run("cat /home/ansible/.ssh/id_rsa.pub", user="ansible")
if exit_code != 0:
    print("❌ Failed to read public key")
else:
    pubkey_str = pubkey.decode().strip()
    for name, role in container_names.items():
        if role == "node":
            print(f"[{name}] Injecting key...")
            containers[name].exec_run(f"bash -c 'echo \"{pubkey_str}\" >> /home/ansible/.ssh/authorized_keys'", user="root")
            containers[name].exec_run("chown -R ansible:ansible /home/ansible/.ssh", user="root")
            containers[name].exec_run("chmod 700 /home/ansible/.ssh", user="root")
            containers[name].exec_run("chmod 600 /home/ansible/.ssh/authorized_keys", user="root")

# Generate Ansible inventory
inventory = "[nodes]\n"
for name, role in container_names.items():
    if role == "node":
        inventory += f"{name}\n"

containers["ansible-machine"].exec_run(f"bash -c 'echo \"{inventory}\" > /etc/ansible/hosts'", user="root")
containers["ansible-machine"].exec_run("chown ansible:ansible /etc/ansible/hosts && chmod 644 /etc/ansible/hosts", user="root")

# Copy Ansible playbook folder into the control node
print("\n📂 Copying Ansible playbook to control node...")
local_ansible_path = "../ansible"  # Ensure this folder exists locally
container_ansible_path = "/home/ansible/ansible"

subprocess.run(["docker", "cp", local_ansible_path, f"ansible-machine:{container_ansible_path}"])
containers["ansible-machine"].exec_run(f"chown -R ansible:ansible {container_ansible_path}", user="root")

# Run Ansible playbook inside the control container
print("\n▶️ Running PostgreSQL Ansible playbook on control node...")
run_playbook_cmd = (
    'su - ansible -c "cd ~/ansible && '
    'ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i /etc/ansible/hosts site.yml"'
)
exit_code, result = containers["ansible-machine"].exec_run(run_playbook_cmd)
print(result.decode())

# Optional: Save Ansible ping test output

print("\n📡 Testing Ansible connection:")
ping_result = containers["ansible-machine"].exec_run(
    'su - ansible -c "ANSIBLE_HOST_KEY_CHECKING=False ANSIBLE_PYTHON_INTERPRETER=auto_silent ansible nodes -m ping"'
)
output_text = ping_result.output.decode()
print(output_text)
Path("ansible_ping_output.txt").write_text(output_text)
print("📄 ansible_ping_output.txt saved.")
