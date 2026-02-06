# vCenter 8 Certificate Expiration Monitor

A lightweight Python automation tool to monitor TLS certificates across multiple vCenter 8 instances using the native REST API.


## Authors

- Jose Antonio Vico — https://github.com/vicosoft


## ⚙️ How it Works
The script connects to the vCenter API, retrieves the TLS certificate information, and calculates the remaining days of validity.
- **Email Alerts**: Triggered when validity is below 10 days.
- **Log Levels**: Switches from `[INFO]` to `[ERROR]` when validity is below 3 days.

## 🔐 Security & Permissions Setup

To follow the principle of least privilege, perform these steps in each vCenter:

1. **Create User**: Create a local user (e.g., `monitor-cert@vsphere.local`).
2. **Assign Group**: Add the user to the `ReadOnlyUsers` group.
3. **Global Permissions**: 
   - Go to the **Inventory Root** (`/`).
   - Navigate to the **Permissions** tab.
   - Add the user with the **Read-only** role.
   - **Crucial**: Check the box **"Propagate to children"**.

## 🚀 Deployment

### 1. Requirements
Install dependencies from the provided `requirements.txt`:
```bash
pip install -r requirements.txt
```

## crond file

```
# /etc/cron.d/certs.cron: Centralized vCenter Certificate Check
# Permissions: chmod 400 root:root

# Service account password used by the script
VC_PASS="your_secure_password"

# Run once a day at 08:00 AM as root user
00 08 * * * root /usr/bin/python3 /opt/scripts/vcenter_cert_check.py 
```

## Practical Example

Below are example outputs and alert messages for different states. Hostnames are fictional.

Normal output (no imminent expirations):

```bash
# cat /var/log/vcenter*.log
[INFO] Certificates OK on vCenter vcenter01.localdomain.local
[INFO] Certificates OK on vCenter vcenter02.localdomain.local
```

When a certificate reaches the alert threshold (10 days remaining) the script sends an email each time the cron job runs. Example email:

- Subject: ALERT: Certificate Expiration - vcenter01.localdomain.local
- Body: CRITICAL: The certificate for vcenter01.localdomain.local expires in ONLY 10 days (DATE and TIME).

When the certificate reaches the error threshold (3 days remaining) the log level changes to `[ERROR]` and the lines look like this:

```bash
# cat /var/log/vcenter*.log
[ERROR] Certificate expiring soon (3 days) on vCenter vcenter01.localdomain.local
[ERROR] Certificate expiring soon (3 days) on vCenter vcenter02.localdomain.local
```

This behavior allows Pandora FMS to collect logs and display a green indicator for `[INFO]` entries and a red indicator for `[ERROR]` entries. From the logs you can also see the remaining days (from 3 days) or if a certificate has already expired. Level-1 operators can then open an urgent incident or apply KB procedures to renew certificates, while vCenter administrators receive the emails to replace certificates before they expire.


## Manual Certificate Verification

To manually list all certificates on a vCenter instance (useful for verification or cross-checking), connect to the vCenter via SSH and run:

```bash
for i in $(/usr/lib/vmware-vmafd/bin/vecs-cli store list); do echo STORE $i; /usr/lib/vmware-vmafd/bin/vecs-cli entry list --store $i --text | egrep "Alias|Not After"; done
```

This will display all certificate stores and their expiration dates (`Not After`), allowing you to verify the monitored certificates manually or troubleshoot any discrepancies.

