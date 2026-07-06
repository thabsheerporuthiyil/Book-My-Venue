# Configuration Management & Deployment with Ansible

This directory contains the Ansible playbooks and roles used to configure target hosts (VMs) and execute deployments of the containerized services.

---

## Folder Layout

We follow Ansible best practices using standard roles:

```text
infrastructure/ansible/
├── group_vars/
│   ├── all.yml                 # Global configuration values
│   ├── staging.yml             # Staging specific variables (ports, endpoints)
│   └── production.yml          # Production specific hardening rules
├── inventories/
│   ├── staging.ini             # IP listings for staging servers
│   └── production.ini          # IP listings for production servers
├── roles/
│   ├── common/                 # Basic VM provisioning (packages, security, users)
│   ├── docker/                 # Setup Docker engine & Docker Compose CLI
│   └── deploy_services/        # Syncs docker-compose configs and deploys app services
├── site.yml                    # Main playbook routing roles to target hosts
└── README.md
```

---

## How it works with Docker Compose

During deployment, Ansible:
1. Connects to the host VMs (provisioned by Terraform).
2. Sets up Docker, system packages, and users.
3. Synchronizes configuration files (Nginx gateway configs, environment variables).
4. Synchronizes `docker-compose.yml` to the host directory `/opt/bookmyvenue/`.
5. Starts the containers using Ansible's `community.docker.docker_compose` module:
   ```bash
   ansible-playbook -i inventories/staging.ini site.yml --tags deploy
   ```
