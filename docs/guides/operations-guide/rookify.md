---
sidebar_label: Rookify Operation: Migrate to Rook from Ceph Ansible (technical preview)
---

# Use Rookify: Migrate to Rook from Ceph Ansible (technical preview)

:::warning

Rookify is developed to migrate from Ceph-Ansible to Rook _in place_ and _without downtime_.
Nevertheless, it is **strongly advised** to test Rookify in a controlled environment beforehand, such as the [OSISM testbed](https://github.com/osism/testbed). Additionally, ensure that all precautionary backups are taken, and any other necessary safety measures are in place.

:::

The [Rookify GitHub repository](https://github.com/SovereignCloudStack/rookify) includes a README.md that provides a condensed summary of the information covered here.

## Consider using a pickle file

In order to have a trackable state of process you can add a pickle file. Specify this option in the `config.yaml`:

```yaml title="config.example.yaml"
general:
  machine_pickle_file: data.pickle
```

Now you will be able to to view the state of progress by running `rookify --show-state`.

:::warning
    Rookify will take data.pickle as a source of truth for its operations. If you want to start a clean migration, be sure to delete the file.
:::

## Rookify CLI

### Run

:::warning
    Currenlty rookify executes per default
:::

Currenlty rookify executes per default. This means: if you run rookify like so `.venv/bin/rookify`, it will start the migration as configured in `config.yaml`.

### --dry-run

:::tip
    Run preflight-mode to check if Rookify can connect to your target systems
:::

Rookify has a `preflight-mode` to check if basic commands and the connection to the target systems are working.
You can always run `--dry-run` mode, without any danger that migration processes will be executed.

### --help

Run `--help` to see the various options the CLI provides.

### --show

Run `--show` if you used a pickel-file (see the configuration-guide concerning the general section). This will show the status of your migration process.

## Debugging and Testing

If you suspect that something is not working in Rookify itself, you can start setting logging to `DEBUG`.

If you suspect that something is not working in Rookify itself, you could start by running the tests. For this you need to have access to rookifies code.

### Set logging to debug level

Edit the `config.yaml` and set level to "DEBUG":

```yaml title="config.example.yaml"
logging:
  level: DEBUG
  format:
    time: "%Y-%m-%d %H:%M.%S" # other example: "iso"
    renderer: console # or: json
```

You can also set the other formatting options, as indicated by the comments, for further options take a look a the documentation of [structlog](https://www.structlog.org/en/stable/standard-library.html).

### Run tests

Make sure you can reach Rookifies code on you system. Then you can either:

1. run `make run-tests-locally` from the working directory of the rookify repository. If you prefer to use a containerized setup, use `make run-tests`.
2. run `.venv/bin/python -m pytest` from the virtual environment of you installation
