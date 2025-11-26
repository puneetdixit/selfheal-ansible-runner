import ansible_runner
import os
import json

FULL_PAYLOAD_STRING = os.environ.get('FULL_PAYLOAD')
CUSTOM_ID = os.environ.get('CUSTOM_RUN_ID', 'API-TRIGGER-DEFAULT')

if not FULL_PAYLOAD_STRING:
    print("Error: FULL_PAYLOAD environment variable not found.")
    exit(1)

try:
    extra_vars_payload = json.loads(FULL_PAYLOAD_STRING)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON payload: {e}")
    exit(1)

extra_vars_payload['custom_run_id'] = CUSTOM_ID 

INVENTORY_FILE = 'inventory.ini'
PLAYBOOK_FILE = 'playbook.yml' 

print(f"Starting Ansible Runner for custom ID: {CUSTOM_ID}")
print(f"Passing Extra Vars: {json.dumps(extra_vars_payload, indent=2)}")

# # --- Execute Ansible Runner ---
# r = ansible_runner.run(
#     private_data_dir=os.getcwd(), 
#     inventory=INVENTORY_FILE,
#     playbook=PLAYBOOK_FILE,
#     extravars=extra_vars_payload,
# )
