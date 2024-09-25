---
sidebar_label: Configure Rookify: Migrate to Rook from Ceph Ansible (technical preview)
sidebar_position: 31
---

# Configure Rookify: Migrate from Ceph Ansible to Rook (Technical Preview)

The [Rookify GitHub repository](https://github.com/SovereignCloudStack/rookify) includes a README.md that provides a condensed summary of the information covered here.

Rookify is developed to migrate from Ceph-Ansible to Rook _in place_ and _without downtime_.

Nevertheless, it is **strongly advised** to test Rookify in a controlled environment beforehand, such as the [OSISM testbed](https://github.com/osism/testbed). Additionally, ensure that all precautionary backups are taken, and any other necessary safety measures are in place.

## Config.yaml

The primary configuration file for Rookify is `config.yaml`. The repository contains an example file for general use, as well as one specifically tailored to the OSISM testbed setup:

- [config.example.yaml](https://github.com/SovereignCloudStack/rookify/blob/main/config.example.yaml)
- [config.example.osism.yaml](https://github.com/SovereignCloudStack/rookify/blob/main/config.example.osism.yaml)

### Parameters

```yaml
general:
  machine_pickle_file: data.pickle
```

The general section allows for optional definition of a pickle file, which allows for saving the state of the migration as serialized objects on disk. The pickle filed can be named as pleased.

```yaml
logging:
  level: INFO # level at which logging should start
  format:
    time: "%Y-%m-%d %H:%M.%S" # other example: "iso"
    renderer: console # or: json
```

The `logging` section allows for specification of `structlog`. The `level` parameter can be set to all python [log-levels](https://docs.python.org/3/library/logging.html#logging-levels), i.e. `NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAl`, but it is recommended to use `INFO`.

```yaml
ceph:
  config: ./.ceph/ceph.conf
  keyring: ./.ceph/ceph.client.admin.keyring
```

The `ceph` section specifies the `ceph.conf` and `ceph.client.admin.keyring` of the target systems (i.e. the system where Ceph-Ansible needs to be migrated to Rook).
