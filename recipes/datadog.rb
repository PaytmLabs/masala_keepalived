#
# Cookbook Name:: masala_haproxy
# Recipe:: datadog
#
# Copyright 2016, Paytm Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

primary_if = node['network']['interfaces'][node['system']['primary_interface']]
primary_addrs = primary_if['addresses']
primary_addrs_ipv4 = primary_addrs.select { |_addr, attrs| attrs['family'] == 'inet' }
primary_ip = primary_addrs_ipv4.keys.first

if node['masala_base']['dd_enable'] and not node['masala_base']['dd_api_key'].nil?

  # If datadog still shipping 4.2.5 PySNMP, upgrade it
  execute "upgrade datadog embedded PySNMP" do
    command "/opt/datadog-agent/embedded/bin/pip install --upgrade pysnmp"
    only_if { Dir.exists?('/opt/datadog-agent/embedded/lib/python2.7/site-packages/pysnmp-4.3.5-py2.7.egg-info') }
  end

  execute "compile KEELALIVED-MIB to PySNMP format" do
    command "/opt/datadog-agent/bin/mibdump.py SNMPv2-SMI KEEPALIVED-MIB"
    user 'dd-agent'
    not_if { File.exists?('/opt/datadog-agent/.pysnmp/mibs/KEEPALIVED-MIB.py') }
  end

  cookbook_file '/etc/dd-agent/checks.d/keepalived_vrrp.py' do
    source 'keepalived_vrrp.py'
    owner 'root'
    group node.root_group
    mode '0755'
    action :create
    notifies :restart, "service[datadog-agent]"
  end

  template "/etc/dd-agent/conf.d/keepalived_vrrp.yaml" do
    source  "keepalived_vrrp.yaml.erb"
    owner 'root'
    group node.root_group
    mode  00644
    notifies :restart, "service[datadog-agent]"
  end

end

