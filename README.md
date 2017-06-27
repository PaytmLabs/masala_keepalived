# masala_keepalived

This is a component of the [masala toolkit](https://github.com/PaytmLabs/masala).

This is a [wrapper cookbook](http://blog.vialstudios.com/the-environment-cookbook-pattern/#thewrappercookbook) for providing recipes for a simplified configuration for keepalived to manage an active/standby pair.

It is meant to be added to a 'keepalive' recipe for a given service (IE: haproxy) which that
recipe might use to add support for itself to run in an active/standby HA configuration.

## Supported Platforms

The platforms supported are:
- Centos 6.7+ / Centos 7.1+
- Ubuntu 14.04 LTS (And future LTS releases)
- Debian 8.2+

Only Centos versions see active support and testing at this time.

## Attributes

Please also see the documentation for the cookbooks included by masala_keepalived. (See [metadata.rb](https://github.com/PaytmLabs/masala_keepalived/blob/develop/metadata.rb) file)

<table>
  <tr>
    <th>Key</th>
    <th>Type</th>
    <th>Description</th>
    <th>Default</th>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['name']</tt></td>
    <td>String</td>
    <td>A name/label for the keepalive instance</td>
    <td><tt>a_router</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['state']</tt></td>
    <td>String</td>
    <td>Valid options are MASTER and BACKUP, and sets the preferred state for the keepalive instance</td>
    <td><tt>MASTER</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['priority']</tt></td>
    <td>Integer</td>
    <td>Priority level, influences which node will take over during a transition event</td>
    <td><tt>101</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['advert_int']</tt></td>
    <td>Integer</td>
    <td>VRRP Advertisment interval in seconds. How frequently nodes will broadcast their status.</td>
    <td><tt>1</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['nopreempt']</tt></td>
    <td>Boolean</td>
    <td>Flag to control pre-emption. If false, a backup that has taken over will not fail back until it experiences failure itself. If true, the defined master node will always attempt to take over the VIP</td>
    <td><tt>false</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['auth_type']</tt></td>
    <td>String</td>
    <td>Type of authentication to use for VRRP advertisments. Valid choices are PASS (recommended), and AH (discouraged)</td>
    <td><tt>PASS</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['auth_pass']</tt></td>
    <td>String</td>
    <td>The actual password that will be used to secure VRRP advertisments between keepalive instances</td>
    <td><tt>abc123</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['aws']</tt></td>
    <td>Boolean</td>
    <td>A flag to indicate if AWS support should be enabled. If enabled, a hook will be added to keepalived to call the AWS API to enable VIP reassignments.</td>
    <td><tt>false</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_1'][*]</tt></td>
    <td>Hash</td>
    <td>Configuration for the primary virtual interface</td>
    <td><tt>See below</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_1']['virtual_router_id']</tt></td>
    <td>Integer</td>
    <td>Identifier for the virtual router. Must be the same within a keepalive group, and different between groups</td>
    <td><tt>10</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_1']['vip']</tt></td>
    <td>String</td>
    <td>Virtual IP address to be used for this virtual router</td>
    <td><tt>nil</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_1']['track_script']</tt></td>
    <td>String</td>
    <td>The label for the tracking script used by the instance to determine it's health</td>
    <td><tt>chk_init</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_1']['peer']</tt></td>
    <td>String</td>
    <td>IP address of the peer node for this keepalive group.</td>
    <td><tt>nil</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_1']['interface']</tt></td>
    <td>String</td>
    <td>Name of the physical network interface that the virtual IP will be bound to.</td>
    <td><tt>nil</tt></td>
  </tr>
  <tr>
    <td><tt>['masala_keepalived']['vi_2'][*}</tt></td>
    <td>Hash</td>
    <td>Configuration for the secondary virtual interface, follows the same structure as the primary, see above.</td>
    <td><tt>nil</tt></td>
  </tr>
</table>

## Usage

### masala_keepalived::default

Include `masala_keepalived` in your node's `run_list`:

```json
{
  "run_list": [
    "recipe[masala_keepalived::default]"
  ]
}
```

## License, authors, and how to contribute

See:
- [LICENSE](https://github.com/PaytmLabs/masala_keepalived/blob/develop/LICENSE)
- [MAINTAINERS.md](https://github.com/PaytmLabs/masala_keepalived/blob/develop/MAINTAINERS.md)
- [CONTRIBUTING.md](https://github.com/PaytmLabs/masala_keepalived/blob/develop/CONTRIBUTING.md)

