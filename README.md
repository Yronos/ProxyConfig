[English](https://github.com/Yronos/ProxyConfig/blob/main/README.md) | [中文](https://github.com/Yronos/ProxyConfig/blob/main/README_zh.md)
# ProxyConfig

Based on modularity, you can combine and match in the following order, adjusting the configuration as needed.

1. BasicSettings.yaml
2. dns.yaml
3. proxy-groups.yaml
4. rules.yaml
5. rule-providers.yaml
6. proxy-providers.yaml (this module can be omitted if using client software, such as [sub-store](https://github.com/sub-store-org/Sub-Store))

# The following are some examples:

The configuration has a relatively complete core basic setting and a comprehensive DNS diversion setting, with the proxy-groups section having a relatively complete software diversion, and the rules and rule-providers sections refer to the design of [author Sukka](https://github.com/sukkaw).

The following configuration only differs in the proxy-groups section, with other parts unchanged, allowing for personal modifications based on individual needs:

## mihomo.yaml

Includes proxy-groups for common regions (**Hong Kong, Taiwan, Japan, Singapore, USA, South Korea**)

## mihomoPlus.yaml

Includes proxy-groups for most regions (**Hong Kong, Taiwan, Japan, Singapore, USA, South Korea, UK, Germany, France, Netherlands, Europe manual, Europe automatic**)

## mihomoPro.yaml

Includes proxy-groups for most regions (**Hong Kong, Taiwan, Japan, Singapore, USA, South Korea, UK, Germany, France, Netherlands, Europe manual, Europe automatic**) as well as **load balancing** strategies for some regions (**Hong Kong, Taiwan, Japan, and Hong Kong-Taiwan-Japan combination**), where the load balancing includes **polling** (`which will distribute all requests to different proxy nodes within the strategy group`) and **hashing** (`which will assign requests with the same target address to the same proxy node within the strategy group`), refer to [kernel configuration](https://wiki.metacubex.one/config/proxy-groups/load-balance/).

## mihomoProMax.yaml

Includes proxy-groups for most regions (**Hong Kong, Taiwan, Japan, Singapore, USA, South Korea, UK, Germany, France, Netherlands, Europe manual, Europe automatic**) as well as **load balancing** strategies for most regions (**Hong Kong, Taiwan, Japan, Hong Kong-Taiwan-Japan combination, South Korea, Singapore, USA, obscure regions combination**), where the load balancing includes **polling** (`which will distribute all requests to different proxy nodes within the strategy group`) and **hashing** (`which will assign requests with the same target address to the same proxy node within the strategy group`), refer to [kernel configuration](https://wiki.metacubex.one/config/proxy-groups/load-balance/).
