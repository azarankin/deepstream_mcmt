 #disable ip v6
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
registry refresh
# deepstream debug
export GST_DEBUG="nvmsgbroker:5,nvmsgconv:5"
#gxf_server --host 0.0.0.0 --port 50051
