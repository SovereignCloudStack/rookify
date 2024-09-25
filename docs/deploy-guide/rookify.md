---
sidebar_label: Deploy Rookify: Migrate to Rook from Ceph Ansible (technical preview)
sidebar_position: 51
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Deploy Rookify: Migrate to Rook from Ceph Ansible (technical preview)

:::warning

Rookify is developed to migrate from Ceph-Ansible to Rook _in place_ and _without downtime_.
Nevertheless, it is **strongly advised** to test Rookify in a controlled environment beforehand, such as the [OSISM testbed](https://github.com/osism/testbed). Additionally, ensure that all precautionary backups are taken, and any other necessary safety measures are in place.

:::

Rookify is now available in the SCS Reference Implementation (OSISM) and can be deployed as shown in the [paragraph below](#using-the-scs-reference-implementation-osism).

The [Rookify GitHub repository](https://github.com/SovereignCloudStack/rookify) includes a README.md that provides a condensed summary of the information covered here.

## Using the SCS Reference Implementation (OSISM)

:::info

Rookify will be available in OSISM and will be deployable usin osism-commands based on ansible configurations.

:::

But is is not available yet ;)

## Manual Installation

### Download or Clone the Repository

Clone or download Rookify from the [repository](https://github.com/SovereignCloudStack/rookify).

:::tip

Checkout the included options of the added `Makefile` by simply typing `make`.

:::

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

:::tip

Before running rookify, first check all options by using `rookify --help`

:::

To run rookify you can either run it directly from within pythons virtualenv or with help of the make file:

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

:::note

Before running rookify, it can be usefull to check all options by using `rookify --help`

:::
