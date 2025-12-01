import ansible_runner
import os
import json
import subprocess
import requests
import signal
import sys

PAYLOAD_STRING = os.environ.get('PAYLOAD')
INVENTORY_FILE = 'inventory.ini'
PLAYBOOK_FILE = 'playbook.yml'
CONFIG_PATH = 'ansible.cfg'
DEFAULT_SSH_USER = 'ubuntu'
DEFAULT_SSH_CONNECTION = 'ssh'


try:
    extra_vars_payload = json.loads(PAYLOAD_STRING)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON payload: {e}")
    exit(1)

custom_run_id = extra_vars_payload.pop('custom_run_id', 'NO_ID_FOUND')
hosts_list = extra_vars_payload['hosts']

print(f"Starting Ansible Runner for custom run ID: {custom_run_id}")
print(f"Target Hosts: {hosts_list}")
print(f"Passing Extra Vars: {json.dumps(extra_vars_payload, indent=2)}")

def create_dynamic_inventory(hosts: list, inventory_path: str):
    """
    Creates the inventory file dynamically. Keys are handled by the SSH Agent.
    """
    if not hosts:
        print("Error: Host list is empty. Cannot create inventory.")
        return False
    
    host_ip = hosts[0]
    host_line = f"{host_ip}" 
    
    inventory_content = f"""
[all:vars]
ansible_connection={DEFAULT_SSH_CONNECTION}
ansible_user={DEFAULT_SSH_USER}
ansible_ssh_args='-o ForwardAgent=yes -o StrictHostKeyChecking=no -l {DEFAULT_SSH_USER}'

[all]
{host_line}
"""
    
    try:
        with open(inventory_path, 'w') as f:
            f.write(inventory_content.strip())
        print(f"Successfully created dynamic inventory file: {inventory_path}")
        return True
    except IOError as e:
        print(f"Error writing inventory file: {e}")
        return False

if not create_dynamic_inventory(hosts_list, INVENTORY_FILE):
    exit(1)


# runner_env = os.environ.copy()
# runner_env["ANSIBLE_CONFIG"] = CONFIG_PATH

# # 2. Execute Ansible Runner
# r = ansible_runner.run(
#     private_data_dir=os.getcwd(), 
#     inventory=INVENTORY_FILE,
#     playbook=PLAYBOOK_FILE,
#     extravars=extra_vars_payload,
#     envvars=runner_env 
# )


# # --- Process Output and Status (Equivalent to your final print block) ---
# process_output = []

# # Stream the output for logging
# for line in r.stdout.splitlines():
#     print(line, flush=True)
#     process_output.append(line)
# for line in r.stderr.splitlines():
#     print(line, flush=True)

# status = r.status
# rc = r.rc

# print(f"\n--- Ansible Runner Summary ---")
# print(f"Status: {status}")
# print(f"Return Code: {rc}")

# if status == 'successful':
#     exit(0)
# else:
#     # Print full stdout for debugging failure
#     print(f"\n--- Full Runner Event Output (STDOUT) ---")
#     print(r.stdout.read())
#     exit(1)



cmd = ["ansible-playbook", "-i", INVENTORY_FILE, PLAYBOOK_FILE, "-e", json.dumps(extra_vars_payload, separators=(",", ":"))]
env = os.environ.copy()
env["ANSIBLE_CONFIG"] = CONFIG_PATH
process_output = []

popen_kwargs = dict(
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    env=env,
)

popen_kwargs["preexec_fn"] = os.setsid

proc = subprocess.Popen(cmd, **popen_kwargs)

try:
    stdout, _ = proc.communicate(timeout=120)
except subprocess.TimeoutExpired as e:
    # timed out: try graceful shutdown of the process group then force-kill
    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
    except Exception:
        pass

    try:
        stdout, _ = proc.communicate(timeout=5)
    except Exception:
        stdout = getattr(e, "stdout", None) or ""
        # force kill if still alive
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except Exception:
            pass

if stdout is None:
    stdout = ""

for line in stdout.splitlines():
    print(line, flush=True)
    process_output.append(line)

try:
    proc.wait(timeout=1)
except Exception:
    # still alive: try to force kill
    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        else:
            proc.kill()
    except Exception:
        pass
    proc.wait()

rc = proc.returncode
status = "success" if rc == 0 else "failed"

print(f"Status : {status}, output : {process_output}")

# --- Send status and logs to the configured API ---
api_url = "http://3.231.210.224:8000/github-actions/results"
payload = {
    "custom_run_id": custom_run_id,
    "status": status,
    "rc": rc,
    "logs_text": "\n".join(process_output),
}

headers = {
    "Content-Type": "application/json",
}

try:
    resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
    print(f"Posted results to {api_url} - status_code: {resp.status_code}")
    try:
        print("Response:", resp.text)
    except Exception:
        pass
except requests.RequestException as e:
    print(f"Failed to POST results to {api_url}: {e}")

# Exit with the same code as the ansible-playbook process
if rc == 0:
    sys.exit(0)
else:
    sys.exit(1)
