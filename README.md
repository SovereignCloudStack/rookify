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
  - Kubernetes nodes should be rolled out at least on the OSD nodes
- Rook operator version 1.13 or higher installed in the Kubernetes cluster.

## Installation
1. Clone the repository:
```bash
git clone https://github.com/SovereignCloudStack/rookify
```

2. Navigate to the tool directory:
```bash
cd rookify
```

3. __TODO:__ Install script

## Usage
__TODO__

## Support
For issues, questions, or contributions, please open an issue or pull request in the GitHub repository. We welcome community feedback and contributions to enhance rookify.

## License
__TODO__