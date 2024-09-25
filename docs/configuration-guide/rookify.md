---
sidebar_label: Configure Rookify: Migrate to Rook from Ceph Ansible (technical preview)
sidebar_position: 31
---

# Configure Rookify: Migrate from Ceph Ansible to Rook (Technical Preview)

:::warning

Rookify is developed to migrate from Ceph-Ansible to Rook _in place_ and _without downtime_.
Nevertheless, it is **strongly advised** to test Rookify in a controlled environment beforehand, such as the [OSISM testbed](https://github.com/osism/testbed). Additionally, ensure that all precautionary backups are taken, and any other necessary safety measures are in place.

:::

The [Rookify GitHub repository](https://github.com/SovereignCloudStack/rookify) includes a README.md that provides a condensed summary of the information covered here.

## Config.yaml

The primary configuration file for Rookify is `config.yaml`. The repository contains an example file for general use, as well as one specifically tailored to the OSISM testbed setup:

- [config.example.yaml](https://github.com/SovereignCloudStack/rookify/blob/main/config.example.yaml)
- [config.example.osism.yaml](https://github.com/SovereignCloudStack/rookify/blob/main/config.example.osism.yaml)

### Parameters

#### General

```yaml title="config.example.yaml"
general:
  machine_pickle_file: data.pickle
```

The general section allows for optional definition of a pickle file, which allows for saving the state of the migration as serialized objects on disk. The pickle filed can be named as pleased.

#### Logging

```yaml title="config.example.yaml"
logging:
  level: INFO # level at which logging should start
  format:
    time: "%Y-%m-%d %H:%M.%S" # other example: "iso"
    renderer: console # or: json
```

The `logging` section allows for specification of `structlog`. The `level` parameter can be set to all python [log-levels](https://docs.python.org/3/library/logging.html#logging-levels), i.e. `NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAl`, but it is recommended to use `INFO`.

#### Ceph

```yaml title="config.example.yaml"

ceph:
  config: ./.ceph/ceph.conf
  keyring: ./.ceph/ceph.client.admin.keyring
```

The `ceph` section specifies the `ceph.conf` and `ceph.client.admin.keyring` of the target systems (i.e. the system where Ceph-Ansible needs to be migrated to Rook).

#### SSH

```yaml title="config.example.yaml"
# fill in correct path to private key
ssh:
  private_key: /home/USER/.ssh/cloud.private
  hosts:
    testbed-node-0:
      address: 192.168.16.10
      user: dragon
    testbed-node-1:
      address: 192.168.16.11
      user: dragon
    testbed-node-2:
      address: 192.168.16.12
      user: dragon
```

The `ssh` section requires specification of the `private_key` and `hosts`. The `hosts` section specifies the hostnames or aliases (e.g. keys like `testbed-node-0`), their ip-addresses (e.g. if rookify connects to the target systems per VPN add ips starting with `192.186...`) and user for login. If you are using the OSISM testbed, make sure that the private key does not contain any `EOF` or other strings, i.e. make sure the keys are 'clean' to avoid connection errors.

#### Kubernetes

```yaml title="config.example.yaml"

kubernetes:
  config: ./k8s/config
```

The `kubernetes` section specifies the kubernetes configuration (e.g. if you use kubectl it is located in `~/.kube/config`) for rookifies kubernetes library. Rookify needs to connect to the kubernetes cluster on the target systems in order to use Rook.

```yaml title="config.example.yaml"
rook:
  cluster:
    name: osism-ceph
    namespace: rook-ceph
  ceph:
    image: quay.io/ceph/ceph:v18.2.1
```

The `rook` sections requires some information about the Rook installation on the target system. Concerning the `cluster` Rookify needs to know the cluster-name and cluster-namespace. Rookify also needs to know the ceph version used by Rookify, i.e. the image version of the ceph container.

_Note_: Rookify does not install Rook for you. You need to provide a running Rook, i.e. a Rook Operator, on you target system.

_Note_: For OSISM specific migrations, Rookify needs to have some additional information, i.e. the respective labels for the rook resources:

```yaml title="config.example.osism.yaml"
rook:
  cluster:
    name: osism-ceph
    namespace: rook-ceph
    mds_placement_label: node-role.osism.tech/rook-mds
    mgr_placement_label: node-role.osism.tech/rook-mgr
    mon_placement_label: node-role.osism.tech/rook-mon
    osd_placement_label: node-role.osism.tech/rook-osd
    rgw_placement_label: node-role.osism.tech/rook-rgw
  ceph:
    image: quay.io/ceph/ceph:v18.2.1
```


#### Migration_modules

```yaml title="config.example.yaml"
migration_modules:
- analyze_ceph
- create_rook_cluster
- migrate_mons
- migrate_osds
- migrate_osd_pools
- migrate_mds
- migrate_mds_pools
- migrate_mgrs
- migrate_rgws
- migrate_rgw_pools
```

Rookify is designed to use a modular structure. It has contains various modules to migrate parts of Ceph-Ansible to Rook. The `migration_modules` section specifies which modules need to be run for the migration. Rookify contains more modules, take a look at the [`src/rookify/module`](https://github.com/SovereignCloudStack/rookify/tree/main/src/rookify/modules) directory to see the ones that are currently implemented.

_NOTE_: Many modules are dependent of each other. This means that some models will implicitly run other modules. For example: the `analyze_ceph` module specified above, will be run by all the modules. This means, that one does not need to specify it. It was added here only for reasons of clearity.
