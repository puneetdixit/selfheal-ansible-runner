import ansible_runner
import os
import json

PAYLOAD_STRING = os.environ.get('PAYLOAD')
INVENTORY_FILE = 'inventory.ini'
PLAYBOOK_FILE = 'playbook.yml' 
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
    Creates the inventory file dynamically, defining connection details 
    only for the first host (hosts[0]). Keys are handled by the SSH Agent.
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
ansible_ssh_args='-o ForwardAgent=yes'

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


r = ansible_runner.run(
    private_data_dir=os.getcwd(), 
    inventory=INVENTORY_FILE,
    playbook=PLAYBOOK_FILE,
    extravars=extra_vars_payload,
)

if r.status == 'successful':
    print(f"Ansible run successful! Status: {r.status}")
else:
    print(f"Ansible run failed! Status: {r.status}")
print(r.stdout.read())
exit(1)
