# Proactive Remediation & Automation Playbooks

trigger prediction -> trigger_listener.py -> Ansible playbook -> AWS action -> logs.

| Warning action | Playbook | What happens |
|---|---|---|
| `resize_up` | playbooks/resize_instance.yml | stop -> bigger type -> start |
| `resize_down` | playbooks/resize_instance.yml | same, smaller |
| `load_shift` / `load_restore` | playbooks/load_shift.yml | needs an nginx load balancer + SSH (not available yet) |


## 1. Install (Ubuntu / WSL)
```
cd ~/ansible_playbooks
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
ansible-galaxy collection install -r requirements.yml
```

## 2. Every time you open a new Ubuntu window
```
cd ~/ansible_playbooks
source venv/bin/activate
export AWS_ACCESS_KEY_ID=PASTE_HERE
export AWS_SECRET_ACCESS_KEY=PASTE_HERE
export AWS_DEFAULT_REGION=ap-south-1
```

## 3. Check AWS access and take the BEFORE proof
```
ansible-playbook playbooks/aws_status.yml | tee logs/before.txt
```
Also screenshot EC2 -> Instances (Instance type column).

## 4. Practice (no changes)
Window 1:  `DRY_RUN=true uvicorn trigger_listener:app --port 8500`
Window 2:  `./send_test_trigger.sh`
(No AWS keys? use `MOCK=true` instead of `DRY_RUN=true`. That is a simulation only, not real proof.)

## 5. Real resize
Window 1:  Ctrl+C, then `uvicorn trigger_listener:app --host 0.0.0.0 --port 8500`
Window 2:  `./send_test_trigger.sh`           (Mumbai)
           `./send_test_trigger.sh sample_trigger_virginia.json`   (N. Virginia)
Wait 2-5 minutes per resize.

## 6. AFTER proof and report
```
ansible-playbook playbooks/aws_status.yml | tee logs/after.txt
python generate_report.py
```

## 7. Clean up (go back to the original size)
```
./send_test_trigger.sh sample_trigger_resize_down.json
```

## Notes
- Resize restarts the server. Its public IP will change unless it is an Elastic IP, so
  15.252.164.35 / 18.232.158.190 may be different afterwards. Check with aws_status.yml.
- Allowed sizes are in size_ladder in resize_instance.yml (t3.micro ... t3.xlarge).
  If the workers use another family (e.g. t2), edit that list to match.
