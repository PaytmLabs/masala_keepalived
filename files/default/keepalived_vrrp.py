
# Ensure following run before this script can work:
#
#  /opt/datadog-agent/embedded/bin/pip install --upgrade pysnmp
#
#  sudo -u dd-agent /opt/datadog-agent/bin/mibdump.py SNMPv2-SMI KEEPALIVED-MIB

import re
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.hlapi import SnmpEngine, ContextData, nextCmd, getCmd
from pysnmp.hlapi import ObjectType, ObjectIdentity
from pysnmp.smi import builder
from pysnmp.smi.exval import noSuchInstance, noSuchObject
from pysnmp.error import PySnmpError
import pysnmp.proto.rfc1902 as snmp_type

# project
from checks.network_checks import NetworkCheck, Status
from config import _is_affirmative

# Metric type that we support
SNMP_NUMBERS= frozenset([
  snmp_type.Counter32.__name__,
  snmp_type.Counter64.__name__,
  snmp_type.Gauge32.__name__,
  snmp_type.Unsigned32.__name__,
  snmp_type.Integer.__name__,
  snmp_type.Integer32.__name__,
  'InetAddressPrefixLength',
  'InterfaceIndex'])

SNMP_STRINGS= frozenset([
  'InetAddress',
  'InetAddressType',
  'InetScopeType',
  'VrrpState',
  snmp_type.OctetString.__name__])

SNMP_UNICODE_STRINGS= frozenset([
  'DisplayString'])

VRRP_STATE_TO_INTEGER={
  'init': 0,
  'backup': 1,
  'master': 2,
  'fault': 3,
  'unknown': 4
}

class KeepalivedVrrpCheck(NetworkCheck):
  DEFAULT_RETRIES = 5
  DEFAULT_TIMEOUT = 1
  SC_STATUS = 'keepalived.vrrp.can_check'
  SOURCE_TYPE_NAME = 'system'

  def __init__(self, name, init_config, agentConfig, instances):
    for instance in instances:
      if 'name' not in instance:
        instance['name'] = self._get_instance_key(instance)
        instance['skip_event'] = True

    self.generators = {}

    # Load Custom MIB directory
    self.mibs_path = None
    self.ignore_nonincreasing_oid = False
    if init_config is not None:
      self.mibs_path = init_config.get("mibs_folder")
      self.ignore_nonincreasing_oid = _is_affirmative(
        init_config.get("ignore_nonincreasing_oid", False))
 
    NetworkCheck.__init__(self, name, init_config, agentConfig, instances)

  def _load_conf(self, instance):
    tags = instance.get("tags", [])
    ip_address = instance["ip_address"]
    timeout = int(instance.get('timeout', self.DEFAULT_TIMEOUT))
    retries = int(instance.get('retries', self.DEFAULT_RETRIES))
    enforce_constraints = _is_affirmative(instance.get('enforce_mib_constraints', True))

    if 'verify' in instance and 'weight' in instance:
      self.raise_on_error_indication('VRRP ERROR: Can not combine use of weight and verify parameters.', instance)
    if 'verify' in instance and instance['verify'] not in ('master', 'backup'):
      self.raise_on_error_indication('VRRP ERROR: verify parameter value must be "master" or "backup"', instance)

    instance_key = instance['name']
    cmd_generator = self.generators.get(instance_key, None)
    if not cmd_generator:
      cmd_generator = self.create_command_generator(self.mibs_path, self.ignore_nonincreasing_oid)
      self.generators[instance_key] = cmd_generator

    return cmd_generator, ip_address, tags, timeout, retries, enforce_constraints

  # key is name, or absent that, some combo of ip/host and port
  def _get_instance_key(self, instance):
    key = instance.get('name', None)
    if key:
      return key
    host = instance.get('host', None)
    ip = instance.get('ip_address', None)
    port = instance.get('port', None)
    if host and port:
      key = "{host}:{port}".format(host=host, port=port)
    elif ip and port:
      key = "{host}:{port}".format(host=ip, port=port)
    elif host:
      key = host
    elif ip:
      key = ip
    return key

  @classmethod
  def hex2inet(cls, hexstr):
    ip = int(hexstr, 16)
    octs = []
    for i in range(0, 4):
      octs.insert(0, str(ip & 0xFF))
      ip = ip >> 8
    return ".".join(octs)

  @classmethod
  def hex2inet6(cls, hexstr):
    hexstr = hexstr[2:]
    hexstr = hexstr.lower()
    hexstr = re.sub(r"([a-f\d]{4,4})", "$1:", hexstr)
    hexstr = re.sub(r"(:0000)+:", "::", hexstr)
    hexstr = re.sub(r":0+([0-9a-f])", ":$1", hexstr)
    hexstr = re.sub(r"([0-9a-f]):$", "$1", hexstr)
    return '[%s]' % hexstr

  @classmethod
  def get_auth_data(cls, instance):
    # Only SNMP v1 - SNMP v2 for the moment
    # See http://pysnmp.sourceforge.net/docs/current/security-configuration.html
    if "community" in instance:
      # SNMP v1 - SNMP v2
      # See http://pysnmp.sourceforge.net/docs/current/security-configuration.html
      if int(instance.get("snmp_version", 2)) == 1:
        return cmdgen.CommunityData(instance['community'], mpModel=0)
      return cmdgen.CommunityData(instance['community'], mpModel=1)
    else:
      raise Exception("An authentication method needs to be provided")

  def create_command_generator(self, mibs_path, ignore_nonincreasing_oid):
    '''
    Create a command generator to perform all the snmp query.
    If mibs_path is not None, load the mibs present in the custom mibs
    folder. (Need to be in pysnmp format)
    '''
    cmd_generator = cmdgen.CommandGenerator()
    cmd_generator.ignoreNonIncreasingOid = ignore_nonincreasing_oid
    if mibs_path is not None:
        mib_builder = cmd_generator.snmpEngine.msgAndPduDsp.mibInstrumController.mibBuilder
        mib_sources = mib_builder.getMibSources() + (builder.DirMibSource(mibs_path), )
        mib_builder.setMibSources(*mib_sources)
    return cmd_generator

  @classmethod
  def get_transport_target(cls, instance, timeout, retries):
    '''
    Generate a Transport target object based on the instance's configuration
    '''
    if "ip_address" not in instance:
      raise Exception("An IP address needs to be specified")
    ip_address = instance["ip_address"]
    port = int(instance.get("port", 161)) # Default SNMP port
    return cmdgen.UdpTransportTarget((ip_address, port), timeout=timeout, retries=retries)

  def raise_on_error_indication(self, error_indication, instance, fatal=True):
    if error_indication:
      message = "{0} for instance {1}".format(error_indication, instance["ip_address"])
      instance["service_check_error"] = message
      if fatal:
        raise Exception(message)
      else:
        self.warning(message)

  def snmp_to_python_type(self, value):
    snmp_class = value.__class__.__name__
    if snmp_class in SNMP_NUMBERS:
      if snmp_class == 'Integer32':
        pretty = value.prettyOut(value).strip("'")
        if pretty == str(int(value)):
          return int(value)
        else:
          return pretty
      else:
        return int(value)
    elif snmp_class in SNMP_STRINGS:
      return value.prettyOut(value).strip("'")
    elif snmp_class in SNMP_UNICODE_STRINGS:
      return value.prettyOut(value).strip("'").encode('utf-8')
    else:
      # FIXME: should raise or at least warn of this
      return None
  
  # get a table, return as hash of hashes
  def snmp_get_table(self, instance, cmd_generator, table_oid, lookup_names, timeout, retries, enforce_constraints=True):
    #snmpget = cmd_generator.getCmd
    snmpgetnext = cmd_generator.nextCmd
    transport_target = self.get_transport_target(instance, timeout, retries)
    auth_data = self.get_auth_data(instance)
  
    if type(table_oid) != str:
      table_oid = ObjectType(ObjectIdentity(*table_oid)),
    else:
      table_oid = ObjectType(ObjectIdentity(table_oid)),
  
    dIndex = {}
    cmd = nextCmd(SnmpEngine(), auth_data, transport_target, ContextData(), *table_oid, lookupValues=enforce_constraints, lookupNames=lookup_names, lexicographicMode=False)
    for (errorIndication, errorStatus, errorIndex, varBinds) in cmd:
      if errorIndication:
        self.raise_on_error_indication(errorIndication, instance)
      elif errorStatus:
        self.raise_on_error_indication('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'), instance)
      else:
        for varBind in varBinds:
          oid = varBind[0]
          value = varBind[1]
          label = oid.getLabel()
          # Sometimes we key composite key for index, sometimes as seperate elements. Normalize this
          sym = oid.getMibSymbol()
          ridx = sym[-1]
          fidx = list(filter(lambda x: x != None, ridx))
          midx = list(map(lambda x: str(x), fidx))
          key = ".".join(midx)
          if not key in dIndex:
            dIndex[key] = {}
          dIndex[key][label[-1]] = self.snmp_to_python_type(value)
    return dIndex

  # get a single OID and return the value
  def snmp_get(self, instance, cmd_generator, oid, lookup_names, timeout, retries, enforce_constraints=True):
    snmpget = cmd_generator.getCmd
    #snmpgetnext = cmd_generator.nextCmd
    transport_target = self.get_transport_target(instance, timeout, retries)
    auth_data = self.get_auth_data(instance)

    if type(oid) != str:
      oid = cmdgen.MibVariable(*oid),
    else:
      oid = [oid]

    errorIndication, errorStatus, errorIndex, varBinds = snmpget(auth_data, transport_target, *oid, lookupValues=enforce_constraints, lookupNames=lookup_names)

    if errorIndication:
      self.raise_on_error_indication(errorIndication, instance)
    elif errorStatus:
      self.raise_on_error_indication('%s at %s' % (errorStatus.prettyPrint(), errorIndex and varBinds[int(errorIndex) - 1][0] or '?'), instance)
    else:
      return varBinds[0][1]

  def collect_data(self, instance, cmd_generator, lookup_names, timeout, retries, enforce_constraints=True):

    try:
      keepalived = self.snmp_get(instance, cmd_generator, ['KEEPALIVED-MIB', 'version', 0], lookup_names, timeout, retries, enforce_constraints)
      if keepalived == 'No Such Object available on this agent at this OID':
        self.raise_on_error_indication("VRRP CRITICAL: keepalived is not running", instance)

      routerId = self.snmp_get(instance, cmd_generator, ['KEEPALIVED-MIB', 'routerId', 0], lookup_names, timeout, retries, enforce_constraints)

      vit = self.snmp_get_table(instance, cmd_generator, ['KEEPALIVED-MIB', 'vrrpInstanceTable'], lookup_names, timeout, retries, enforce_constraints)
      if not vit or len(vit) == 0:
        self.raise_on_error_indication('VRRP CRITICAL: keepalived does not have a VRRP instance.', instance)

      for key in sorted(list(vit.keys())):
        vr = vit[key]
        for oldkey in list(vr.keys()):
          newkey = re.sub(r'^vrrpInstance', '', oldkey)
          newkey = newkey[0].lower() + newkey[1:]
          vr[newkey] = vr[oldkey]
          del vr[oldkey]
        vr['vips'] = []

      vat = self.snmp_get_table(instance, cmd_generator, ['KEEPALIVED-MIB', 'vrrpAddressTable'], lookup_names, timeout, retries, enforce_constraints)
      if not vat or len(vat) == 0:
        self.raise_on_error_indication('VRRP CRITICAL: keepalived is missing virtual addresses.', instance)
  
      for key in list(vat.keys()):
        (vrIdx, addrIdx) = key.split('.')
        vr = vit[vrIdx]
        if vat[key]['vrrpAddressType'] == 'ipv4':
          vip = self.hex2inet(vat[key]['vrrpAddressValue'])
          vr['vips'].append(vip)
        if vat[key]['vrrpAddressType'] == 'ipv6':
          vip = self.hex2inet6(vat[key]['vrrpAddressValue'])
          vr['vips'].append(vip)
  
      # load VRRP group tables info
      vsgt = self.snmp_get_table(instance, cmd_generator, ['KEEPALIVED-MIB', 'vrrpSyncGroupTable'], lookup_names, timeout, retries, enforce_constraints)
      vsgmt = self.snmp_get_table(instance, cmd_generator, ['KEEPALIVED-MIB', 'vrrpSyncGroupMemberTable'], lookup_names, timeout, retries, enforce_constraints)
      if vsgt:
        for key in list(vsgmt.keys()):
          (grpIdx, gmIdx) = key.split('.')
          vr = vit[gmIdx]
          grp = vsgt[grpIdx]
          vr['syncGroupName'] = grp['vrrpSyncGroupName']
          vr['syncGroupState'] = grp['vrrpSyncGroupState']

      return (keepalived, routerId, vit)

    except PySnmpError as e:
      if "service_check_error" not in instance:
        instance["service_check_error"] = "Fail to collect some metrics: {0}".format(e)
      if "service_check_severity" not in instance:
        instance["service_check_severity"] = Status.CRITICAL
        self.warning("Fail to collect some metrics: {0}".format(e))

  def _check(self, instance):
    cmd_generator, ip_address, tags, timeout, retries, enforce_constraints = self._load_conf(instance)

    if 'weight' in instance:
      instance['vrrp_check_type'] = 'byWeight'
    elif 'verify' in instance:
      instance['vrrp_check_type'] = 'manualVerify'
    else:
      instance['vrrp_check_type'] = 'initialState'

    tags += [
      'vrrp_check_type:{0}'.format(instance['vrrp_check_type'])
    ]

    try:
      self.log.debug("Querying %s for keepalive vrrp data", ip_address)
      (keepalived, routerId, vit) = self.collect_data(instance, cmd_generator, True, timeout, retries, enforce_constraints=enforce_constraints)

      # do reporting end here
      self.log.debug("%s - %s" % (keepalived, routerId))
      self.report_vrrp_metrics(instance, keepalived, routerId, vit, tags)

    except Exception as e:
      if "service_check_error" not in instance:
        instance["service_check_error"] = "Fail to collect metrics for {0} - {1}".format(instance['name'], e)
      self.warning(instance["service_check_error"])
      return [(self.SC_STATUS, Status.CRITICAL, instance["service_check_error"])]
    finally:
      # Report service checks
      if "service_check_error" in instance:
        status = Status.DOWN
        if "service_check_severity" in instance:
          status = instance["service_check_severity"]
        return [(self.SC_STATUS, status, instance["service_check_error"])]
      return [(self.SC_STATUS, Status.UP, None)]

  def report_vrrp_metrics(self, instance, keepalived, routerId, data, tags):
    # Create a reversed index
    name_to_idx = {}
    for key in data:
      name_to_idx[data[key]['name']] = key
  
    for vr_name in sorted(list(name_to_idx.keys())):
      if re.match(instance['include'], vr_name) and not re.match(instance['exclude'], vr_name):
        vr = data[name_to_idx[vr_name]]
        vr['desiredState'] = 'backup'
        if 'verify' in instance:
          vr['desiredState'] = instance['verify']
        elif 'weight' in instance:
          if instance['weight'] <= vr['effectivePriority']:
            vr['desiredState'] = 'master'
        else:
          vr['desiredState'] = vr['initialState']
  
        if vr['state'] != vr['desiredState']:
          if vr['desiredState'] == 'master':
            vr['STATUS'] = 'CRIT'
            vr['STATUS_GUAGE'] = 2
          else:
            vr['STATUS'] = 'WARN'
            vr['STATUS_GUAGE'] = 1
        else:
          vr['STATUS'] = 'OKAY'
          vr['STATUS_GUAGE'] = 0

        # We have all out info, collected and calculated, now it's time to submit
        vr_tags = list(tags)
        vr_tags += [
          'vrrp_router_name:{0}'.format(routerId),
          'vrrp_virtual_router_id:{0}'.format(vr['virtualRouterId']),
          'vrrp_virtual_router_name:{0}'.format(vr['name']),
          'vrrp_sync_group:{0}'.format(vr['syncGroupName']),
          'vrrp_primary_interface:{0}'.format(vr['primaryInterface']),
          'vrrp_initial_state:{0}'.format(vr['initialState']),
          'vrrp_desired_state:{0}'.format(vr['desiredState'])
        ]
        for vip in vr['vips']:
           vr_tags += [ 'vrrp_virtual_ip:{0}'.format(vip) ]
        self.log.debug("tags: %s" % ",".join(vr_tags))
        self.log.debug("state: %s" % VRRP_STATE_TO_INTEGER[vr['state']])
        self.log.debug("base prio: %s" % vr['basePriority'])
        self.log.debug("effective prio: %s" % vr['effectivePriority'])
        self.log.debug("status: %s" % vr['STATUS_GUAGE'])
        self.gauge('keepalived.vrrp.state', VRRP_STATE_TO_INTEGER[vr['state']], vr_tags)
        self.gauge('keepalived.vrrp.priority.base', vr['basePriority'], vr_tags)
        self.gauge('keepalived.vrrp.priority.effective', vr['effectivePriority'], vr_tags)
        self.gauge('keepalived.vrrp.status', vr['STATUS_GUAGE'], vr_tags)

  def report_as_service_check(self, sc_name, status, instance, msg=None):
    sc_tags = ['vrrp_device:{0}'.format(instance["ip_address"])]
    custom_tags = instance.get('tags', [])
    tags = sc_tags + custom_tags
    self.service_check(sc_name, NetworkCheck.STATUS_TO_SERVICE_CHECK[status], tags=tags, message=msg)





