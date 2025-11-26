import ansible_runner
import os
import json

PAYLOAD_STRING = os.environ.get('PAYLOAD')

try:
    extra_vars_payload = json.loads(PAYLOAD_STRING)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON payload: {e}")
    exit(1)

INVENTORY_FILE = 'inventory.ini'
PLAYBOOK_FILE = 'playbook.yml' 

custom_run_id = extra_vars_payload.pop('custom_run_id')
print(f"Starting Ansible Runner for custom run ID: {custom_run_id}")
print(f"Passing Extra Vars: {json.dumps(extra_vars_payload, indent=2)}")



# # --- Execute Ansible Runner ---
# r = ansible_runner.run(
#     private_data_dir=os.getcwd(), 
#     inventory=INVENTORY_FILE,
#     playbook=PLAYBOOK_FILE,
#     extravars=extra_vars_payload,
# )
