# vCenter 8 Certificate Expiration Monitor

A lightweight Python automation tool to monitor TLS certificates across multiple vCenter 8 instances using the native REST API.

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
Ensure you have the `requests` library installed:
```bash
pip install requests