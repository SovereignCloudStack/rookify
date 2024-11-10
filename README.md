# Rookify

> __DISCLAIMER:__ Rookify is in early development state and is not feature-complete. Don't use it in production environments until it is production-ready and tested!

## Overview
Rookify is designed to facilitate a smooth and efficient transition for existing Ceph clusters to a Rook-managed Ceph cluster environment. This tool targets clusters deployed via traditional methods and those set up using the standards of [Sovereign Cloud Stack](https://github.com/SovereignCloudStack/) and reference implementation [OSISM](https://github.com/osism/). By automating the conversion process, this tool aims to minimize downtime and ensure a seamless migration experience.

## Features
- **Automated Conversion**: Simplifies the migration process from a traditional Ceph deployment to a Rook-managed Ceph environment.
- **Minimal Downtime**: Designed to perform migrations with the least possible impact on availability.
- **Preflight Check**: Analyzes existing Ceph clusters and checks if migrations are possible.

## Prerequisites
- A functioning Ceph cluster deployed via traditional methods.
  - __TODO:__ List supported methods
- Access to a Kubernetes cluster with sufficient resources to host the migrated Ceph cluster.
    - Kubernetes nodes should be rolled out at least on the monitor nodes
- Rook operator version 1.13 or higher installed in the Kubernetes cluster.
- _local development enivornment_ requires radoslib version 2.0.0 installed

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SovereignCloudStack/rookify
```

2. Navigate to the tool directory:
```bash
cd rookify
```

3. Check if your host has the correct "radoslib" library installed (if not: then install radoslib version 2.0.0):
```bash
make check-radoslib
```

4. To install the local development environment
(_Note: This will install pre-commit in your local user context_):
```bash
make setup
```

5. To install the container-based environment
```bash
make build-container
```

## Usage

**NOTE**: for testing purposes the [OSISM Testbed](https://github.com/osism/testbed) is used. The `Makefile` and example configuration (`config.example.osism.yaml`) have built in helper functions and examples for this test setup.

### Copy and adapt configuration files

Choose one of the configuration-examples found in the root of the working directory and copy it to `config.yml`:

```
ls config.example.*
# there is a specific example config for the OSISM testbed: config.example.osism.yaml
cp config.example.yml config.yaml
```

_Adapt the config.yml to your need_: especially enter the correct paths for ssh-keys, kubernetes configuration and ceph configuration (all these configuration files need to be provided!).

### Provide needed configuration files from target servers

Copy the needed configuration-files from the servers that need to be migrated from ceph to rook.

_Provide needed configuration files as written in the config.yml._ At least required are:
- ./ceph/ceph.conf (typically found in `/etc/ceph/` on a testbednode)
- ./ceph/ceph.admin.keyring (typically found in `/etc/ceph/` on a testbednode)
- kubernetes config of user (e.g. found in `~/.kube/config`)
- ssh key of the server (found at `./terraform/.id.rsa` in the `testbed` directory)

Note:
- for the testbed there is a helper script to download the configs from the testbed. These helperscripts need correct `.ssh/config` entries to work (take a look at [scripts/osism/get_configs_from_testbed](osism/get_configs_from_testbed.sh) for an example).
- the helper scripts are merely there to help for testing with the [OSISM testbed](https://github.com/osism/testbed) and might not suit your purposes.

### Run Rookify

Now decide on how to run rookify. Either run it from within a container or locally:

```
run-local-rookify
# or
run-rookify
```

Then sit back and wait. Check the [troubleshooting](#troubleshooting) and [support](#support) sections if any issues occur.

For other options you can also check the makefile: Type `make` to get a list of available commands.

### Check status of migration

Use `rookify --show-states` argument to let each module check for its state in the migration

```bash
.venv/bin/rookify --show-states
ceph mon dump: Not analyzed yet
ceph osd dump: Not analyzed yet
OSD devices: Not analyzed yet
```

#### Troubleshooting

**missing Ceph systemd targets:**
- please consult your distribution's documentation in case documented Ceph systemd unit services or targets are missing
- `cephadm install ceph-common ceph-base ceph-mon ceph-mgr ceph-mds radosgw` may help if supported

**frozen state:**
- if the rookify process freezes, check your connections. In the OSISM testbed especially check the vpn-connection (in testbed repository try `make vpn-*`)

**ssh-issues:**
- make sure the id-rsa keys are "clean" and do not contain unexpected strings like "\<\<EOF". E.g. call `ssh-keygen -p -N "" -f ssh.key` to convert and reformat the keyfile to the expected format.
- allow direnv (`direnv allow`) to use `.envrc` or copy and execute the command from the file: this switches off the ssh-agent, which sometimes has too many keys loaded

## Support

For issues, questions, or contributions, please open an issue or pull request in the GitHub repository. We welcome community feedback and contributions to enhance rookify.

## License
This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
