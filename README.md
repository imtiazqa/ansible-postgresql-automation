
# Ansible PostgreSQL Automation

**PostgreSQL Ansible Playbook**  
This repository contains an Ansible Playbook for automating the installation, configuration, and management of PostgreSQL on target machines.  
It also includes utility scripts for runtime operations and node status checks.

---

## 📂 Repository Structure
```

POSTGRESQL\_ANSIBLE\_PLAYBOOK/
│
├── ansible/
│   ├── roles/
│   │   └── postgresql/
│   │       ├── defaults/
│   │       │   └── main.yml        # Default variables for PostgreSQL role
│   │       ├── handlers/
│   │       │   └── main.yml        # Handlers for service restart/reload
│   │       └── tasks/
│   │           ├── main.yml        # Main PostgreSQL setup tasks
│   │           └── users.yml       # PostgreSQL user creation and permissions
│   └── site.yml                    # Main Ansible Playbook entry point
│
├── scripts/
│   ├── ansible\_ping\_output.txt     # Ping output from Ansible hosts
│   └── runtime\_wrknodes.py         # Python script to check/manage worker nodes

````

---

## ✨ Features

- **Dockerized Lab Environment**
  1. 1 Ansible control node (Ubuntu 22.04)
  2. N worker nodes (user-defined)
  3. Automatic creation and setup via Docker

- **Pre-installed Essential Packages**
  1. All nodes: `sudo`, `openssh-server`, `net-tools`, `vim`, `iputils-ping`
  2. Control node only: `ansible`, `sshpass`

- **Automated Configuration & Management**
  1. Automatic passwordless SSH setup between control and worker nodes
  2. Dynamic Ansible inventory generation
  3. Copies local playbook into the control node automatically
  4. Default configurations stored in `defaults/main.yml`

- **PostgreSQL Deployment & User Management**
  1. Installs and configures PostgreSQL via `tasks/main.yml`
  2. Manages OS user accounts via `tasks/users.yml`
  3. Creates PostgreSQL database users via `handlers/main.yml`

- **Additional Automation Tools**
  1. Python script for runtime worker node management
  2. Runs `site.yml` playbook in one command
  3. Saves Ansible ping results to `ansible_ping_output.txt`

---

## 🛠 Prerequisites

- Docker (latest version recommended)
- Python 3 with:
  
  pip install docker

* Ansible role files present in `ansible/roles/postgresql/`

---

## 🚀 Quick Start

1. **Clone the repository**

   git clone https://github.com/<your-username>/postgresql-ansible-playbook.git
   cd postgresql-ansible-playbook/scripts
   

2. **Run the lab setup script**

   python3 runtime_wrknodes.py

   > Enter the number of worker nodes when prompted.

3. **Watch the magic happen**
   The script will:

   * Create containers and network
   * Install dependencies
   * Setup SSH keys
   * Generate inventory
   * Copy your playbook
   * Run the PostgreSQL playbook
   * Test Ansible connectivity

4. **Check ping results**

   cat ansible_ping_output.txt

---


