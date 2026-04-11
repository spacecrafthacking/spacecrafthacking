#!/usr/bin/env bash
set -euo pipefail

# Always target the non-root sudo user if present, otherwise the current user
#if [ "${EUID}" -eq 0 ] && [ -n "${SUDO_USER-}" ]; then
#  TARGET_USER="${SUDO_USER}"
#else
#  TARGET_USER="${USER}"
#fi

#USER_NAME="${TARGET_USER}"
#USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"

USER_NAME="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"

# ensure NVM_DIR is always defined, even if empty
: "${NVM_DIR:=${USER_HOME}/.nvm}"
export NVM_DIR

PROJECT_DIR="${USER_HOME}/ansible-ubuntu"
INVENTORY_FILE="${PROJECT_DIR}/inventory.ini"
PLAYBOOK_FILE="${PROJECT_DIR}/ubuntu-setup.yml"

ANSIBLE_TAGS="${1-}"

ANSIBLE_TAG_ARGS=()
if [ -n "$ANSIBLE_TAGS" ]; then
  ANSIBLE_TAG_ARGS=(--tags "$ANSIBLE_TAGS")
fi

echo "[*] Updating apt and installing Ansible..."
sudo apt update -y
#sudo apt upgrade -y
sudo apt install -y ansible python3-pip python3-dev libffi-dev libssl-dev

mkdir -p "${PROJECT_DIR}"

cat > "${INVENTORY_FILE}" << 'EOF'
[local]
localhost ansible_connection=local
EOF

cat > "${PROJECT_DIR}/ansible.cfg" << 'EOF' 
[defaults] become_ask_pass = True become_prompt = Please enter your sudo password for this setup:  
EOF

cat > "${PLAYBOOK_FILE}" << EOF
---
- name: Setup The Spacecraft Hacker's Handbook lab environment on Ubuntu 24.04
  hosts: local
  become: true
  become_method: sudo

  vars:
    user_name: "${USER_NAME}"
    user_home: "${USER_HOME}"
    tools_dir: "${USER_HOME}/tools"
    mcs_dir: "${USER_HOME}/mcs"
    nvm_dir: "${USER_HOME}/.nvm"

    # Yamcs
    yamcs_git_repo_url: "https://github.com/yamcs/yamcs.git"
    yamcs_project_dir: "{{ mcs_dir }}/yamcs/latest"
    yamcs_webapp_dir: "{{ yamcs_project_dir }}/yamcs-web/src/main/webapp"

    # OpenC3 COSMOS
    openc3_git_repo_url: "https://github.com/OpenC3/cosmos.git"
    openc3_project_dir: "{{ mcs_dir }}/openc3/latest"

    # F'
    fprime_git_repo_url: "https://github.com/nasa/fprime-gds.git" 
    fprime_project_dir: "{{ mcs_dir }}/fprime/latest"

    # Tools
    burp_download_url: "https://portswigger.net/burp/releases/download?product=community&version=2024.6&type=Linux"
    burp_installer_path: "{{ tools_dir }}/burpsuite_community_linux.sh"

  tasks:
    - name: Ensure base directories exist
      file:
        path: "{{ item }}"
        state: directory
        owner: "{{ user_name }}"
        group: "{{ user_name }}"
        mode: "0755"
      loop:
        - "{{ tools_dir }}"
        - "{{ mcs_dir }}"
        - "{{ fprime_project_dir }}"
      tags: [dirs_group]

    - name: Update apt cache
      become: true
      apt:
        update_cache: yes
        cache_valid_time: 3600
      register: apt_update
      retries: 10
      delay: 6
      until: apt_update is succeeded
      tags: [dependencies_group]

#    - name: Upgrade packages
#      apt:
#        upgrade: dist

    # Packages
    - name: Install OpenJDK, Maven, unzip, curl, git, vim, wireshark, gdb, cmake, python3, python3-pip, python3-venv
      apt:
        name:
          - openjdk-11-jdk
          - openjdk-17-jdk
          - maven
          - unzip
          - curl
          - git
          - vim
          - wireshark
          - gdb
          - cmake
          - python3
          - python3-pip
          - python3-venv
          - net-tools
        state: present
      register: apt_pkgs
      retries: 10
      delay: 6
      until: apt_pkgs is succeeded
      tags: [dependencies_group]

    # nvm
    - name: Install nvm for user
      become: false
      shell: |
        git clone https://github.com/nvm-sh/nvm.git "$NVM_DIR"
      args:
        executable: /bin/bash
      tags: [node_group]

    # Node/npm
    - name: Install Node.js 22 via nvm and set as default
      become: false
      shell: |
        . "$NVM_DIR/nvm.sh"
        nvm install 22
        nvm alias default 22
        echo '. "{{ nvm_dir }}/nvm.sh"' >> "{{ home_dir }}/.bashrc"
      args:
        executable: /bin/bash
      tags: [node_group]

    # Docker
    - name: Install prerequisites for Docker repo
      become: true
      apt:
        name:
          - ca-certificates
          - curl
          - gnupg
        state: present
        update_cache: yes
      register: apt_pkgs
      retries: 10
      delay: 6
      until: apt_pkgs is succeeded
      tags: [docker_group]

    - name: Create Docker apt keyring directory
      become: true
      file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"
      tags: [docker_group]

    - name: Add Docker’s official GPG key
      become: true
      get_url:
        url: https://download.docker.com/linux/ubuntu/gpg
        dest: /etc/apt/keyrings/docker.asc
        mode: "0644"
      tags: [docker_group]

    - name: Add Docker apt repository
      become: true
      copy:
        dest: /etc/apt/sources.list.d/docker.sources
        mode: "0644"
        content: |
          Types: deb
          URIs: https://download.docker.com/linux/ubuntu
          Suites: {{ ansible_lsb.codename }}
          Components: stable
          Signed-By: /etc/apt/keyrings/docker.asc
      tags: [docker_group]

    - name: Update apt cache after adding Docker repo
      become: true
      apt:
        update_cache: yes
      register: apt_pkgs
      retries: 10
      delay: 6
      until: apt_pkgs is succeeded
      tags: [docker_group]

    - name: Install Docker Engine and Compose plugin
      become: true
      apt:
        name:
          - docker-ce
          - docker-ce-cli
          - containerd.io
          - docker-buildx-plugin
          - docker-compose-plugin
        state: present
      register: apt_pkgs
      retries: 10
      delay: 6
      until: apt_pkgs is succeeded
      tags: [docker_group]

    - name: Ensure docker group exists
      become: true
      group:
        name: docker
        state: present
      tags: [docker_group]

    - name: Add user to docker group
      user:
        #name: "{{ user_name }}"
        name: "${USER_NAME}"
        groups: docker
        append: yes
        state: present
      tags: [docker_group]

    # Yamcs - latest
    - name: Clone Yamcs git repo
      become: false
      git:
        repo: "{{ yamcs_git_repo_url }}"
        dest: "{{ yamcs_project_dir }}"
        version: "HEAD"
        update: yes
      tags: [yamcs_group]

    - name: Build Yamcs backend
      become: false
      command: mvn clean install -DskipTests

      args:
        chdir: "{{ yamcs_project_dir }}"
      register: maven_result
      ignore_errors: yes
      tags: [yamcs_group]

    - name: Show Yamcs build result
      debug:
        var: maven_result.stdout_lines
      when: maven_result is defined and maven_result.stdout_lines is defined
      tags: [yamcs_group]

    - name: Yamcs webapp npm install
      become: false
      shell: |
        set -e
        export NVM_DIR="{{ user_home }}/.nvm"
        . "$NVM_DIR/nvm.sh"
        cd "{{ yamcs_webapp_dir }}"
        npm install
      args:
        executable: /bin/bash
      register: npm_result
      ignore_errors: yes
      tags: [yamcs_group]

    - name: Yamcs webapp npm build
      become: false
      shell: |
        set -e
        export NVM_DIR="{{ user_home }}/.nvm"
        . "$NVM_DIR/nvm.sh"
        cd "{{ yamcs_webapp_dir }}"
        npm run build
      args:
        executable: /bin/bash
      register: npm_result
      ignore_errors: yes
      tags: [yamcs_group]

    - name: Show npm build result
      debug:
        var: npm_result.stdout_lines
      when: npm_result is defined and npm_result.stdout_lines is defined
      tags: [yamcs_group]

    - name: Ensure /storage directory exists with correct ownership
      become: true
      file:
        path: /storage
        state: directory
        owner: "{{ user_name }}"
        group: "{{ user_name }}"
        mode: "0755"
      tags: [yamcs_group]

    # OpenC3 COSMOS - latest
    - name: Clone OpenC3 git repo
      become: false
      git:
        repo: "{{ openc3_git_repo_url }}"
        dest: "{{ openc3_project_dir }}"
        version: "HEAD"
        update: yes
      tags: [openc3_group]

    # F' - latest
    - name: Install fprime-bootstrap 
      become: false
      shell: |
        set -e
        cd "{{ fprime_project_dir }}"
        pip install fprime-bootstrap --break-system-packages
      args:
        executable: /bin/bash
      tags: [fprime_group]

    - name: Create F' project with fprime-bootstrap (if not present)
      become: false
      shell: |
        set -e
        cd "{{ fprime_project_dir }}"
        printf "test_project\ntest_project\n" | {{ user_home }}/.local/bin/fprime-bootstrap project
        cd test_project
        . fprime-venv/bin/activate
        fprime-util generate
        printf "\n\n\n\n" | fprime-util new --deployment
        fprime-util build
      args:
        executable: /bin/bash
      tags: [fprime_group]

    # Tools
    # Burp
    - name: Download Burp Suite installer
      become: false
      get_url:
        url: "{{ burp_download_url }}"
        dest: "{{ burp_installer_path }}"
        mode: "0755"
      tags: [tools_group, burp_group]
      
    - name: Note about Burp Suite install
      debug:
        msg: >
          Burp Suite installer downloaded to {{ burp_installer_path }}.
          Run it manually with "sudo {{ burp_installer_path }}" to complete the GUI
      tags: [tools_group, burp_group]

    # vscode
    - name: Download VS Code .deb
      become: true
      get_url:
        url: "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
        dest: /tmp/vscode.deb
        mode: "0644"
      tags: [tools_group, vscode_group]

    - name: Install VS Code from .deb
      become: true
      apt:
        deb: /tmp/vscode.deb
        state: present
      tags: [tools_group, vscode_group]

    - name: Remove downloaded VS Code .deb
      become: true
      file:
        path: /tmp/vscode.deb
        state: absent
      tags: [tools_group, vscode_group]

    # GEF
    - name: Install GEF via official installer script
      become: false
      shell: |
        set -e
        bash -c "\$(curl -fsSL https://gef.blah.cat/sh)"
      args:
        executable: /bin/bash
      tags: [tools_group, gef_group]
EOF

echo "[*] Running Ansible playbook..."
cd "${PROJECT_DIR}"
ansible-playbook -i "${INVENTORY_FILE}" "${PLAYBOOK_FILE}" --ask-become-pass "${ANSIBLE_TAG_ARGS[@]}"
