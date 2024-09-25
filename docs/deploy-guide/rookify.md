---
sidebar_label: Deploy Rookify: Migrate to Rook from Ceph Ansible (technical preview)
sidebar_position: 51
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Deploy Rookify: Migrate to Rook from Ceph Ansible (technical preview)

:::warning

This is a technical preview and not recommended for production use yet.

:::

Rookify is now available in the SCS Reference Implementation (OSISM) and can be deployed as shown in the [paragraph below](## Using the SCS Reference Implementation).

In order to manually deploy Rookify you can take a look at the `README.md` file in the [rookify repository](https://github.com/SovereignCloudStack/rookify) or follow the [instructions here](## Manual Installation).

## Using the SCS Reference Implementation (OSISM)

Rookify is now also available in OSISM and can be deployed with the following osism-commands based on the following ansible scripts.
<!-- TODO -->

## Manual Installation

### Download or Clone the Repository

Clone or download Rookify from the [repository](https://github.com/SovereignCloudStack/rookify), then checkout the included options of the added `Makefile` by simply typing `make`.

## Install and Run Locally

1.  Navigate to the tool directory:

```bash
cd rookify
```

2. To install Rookify locally, pythons virtualenv will be used (Note: This will install pre-commit in your local user context):

```
make setup
```

This command also checks if you have the required python library for `radoslib` installed. Make sure to have it installed on your linux distribution.

To run rookify you can either run it directly from within the virtualenv or with help of the make file:

```bash
# directly
./.venv/bin/rookify --help
# using make
make run-local-rookify
```

## Install and Run from within a Container

1.  Navigate to the tool directory:

2. To install Rookify into a container, podman or docker can be used (Note: in both cases pythons library for `radoslib` needs to be installed locally):

```
make check-radoslib
make up
```

This command uses `docker compose`, so make sure you have that installed as well.

To run rookify you can either enter the container and run rookify from there or use `make run-rookify`.
