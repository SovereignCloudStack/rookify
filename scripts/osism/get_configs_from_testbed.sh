# Helperscript: Gets configs from testbed
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

# copy .kube to ./.k8s
scp -r testbed-manager:.kube ./.k8s

# copy /etc/ceph/ from node1 to ./.k8s
ssh testbed-manager "docker cp cephclient:/etc/ceph /tmp/cephclientconfig" && scp -r testbed-manager:/tmp/cephclientconfig ./.ceph && ssh testbed-manager "rm -rf /tmp/cephclientconfig"
