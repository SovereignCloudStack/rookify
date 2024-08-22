# Helperscript: Reset the k3s cluster of the OSISM testbed
#
# NOTE: this is for test purposes and specific for the OISISM testbed
# it requires .ssh/config to be set accordingly, e.g.:
#
# Host testbed-*
#  StrictHostKeyChecking no
#  IdentityFile <id_rsa of testbed>
#  IdentitiesOnly yes
#  user dragon
#
# Host testbed-manager
#  Hostname <ip of manager of testbed>
#
# Host testbed-node-0
#  Hostname 192.168.16.10
#
# Host testbed-node-1
#   Hostname 192.168.16.11
# Host testbed-node-2
#  Hostname 192.168.16.12
#

ssh testbed-node-0 "sudo rm -rf /var/lib/rancher/k3s/server/db/"
ssh testbed-node-1 "sudo rm -rf /var/lib/rancher/k3s/server/db/"
ssh testbed-node-2 "sudo rm -rf /var/lib/rancher/k3s/server/db/"
ssh testbed-manager "nohup /opt/configuration/scripts/deploy/005-kubernetes.sh > ~/005-kubernetes.log 2>&1 &"
ssh testbed-manager "tail -f ~/005-kubernetes.log"
