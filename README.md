[English](https://github.com/Yronos/ProxyConfig/blob/main/README.md) | [Chinese](https://github.com/Yronos/ProxyConfig/blob/main/README_zh.md)

# ProxyConfig

Based on modularization, you can combine and match according to the following order and delete the configuration according to your needs

1. BasicSettings.yaml
2. dns.yaml
3. proxy-groups.yaml
4. rules.yaml
5. rule-providers.yaml
6. proxy-providers.yaml (If you use client software, you can omit this module, such as using [sub-store](https://github.com/sub-store-org/Sub-Store))

# Quick use:

The configuration has relatively complete kernel basic settings and complete DNS diversion settings. The proxy-groups part has relatively complete software diversion. The rules and rule-providers parts refer to Design by [author Sukka](https://github.com/sukkaw).

The following configurations are different only in the proxy-groups part, and the rest are unchanged. You can modify them based on your personal needs:

## config.yaml

Contains proxy-groups for common regions (**Hong Kong, Taiwan, Japan, Singapore, the United States, South Korea**)

##　configPlus.yaml

Contains proxy-groups for most regions (**Hong Kong, Taiwan, Japan, Singapore, the United States, South Korea, the United Kingdom, Germany, France, the Netherlands, European manual, European automatic**)

## configPro.yaml

Contains proxy-groups for most regions (**Hong Kong, Taiwan, Japan, Singapore, the United States, South Korea, the United Kingdom, Germany, France, the Netherlands, European manual, European automatic**) and **load balancing** strategies for some regions (**Hong Kong, Taiwan, Japan, and Hong Kong, Taiwan, and Japan combination**). The load balancing includes **round robin** (`all requests will be assigned to different proxy nodes in the policy group`) and **hashing** (`assign requests with the same target address to the same proxy node in the policy group`). For reference, [Kernel configuration](https://wiki.metacubex.one/config/proxy-groups/load-balance/).

## configProMax.yaml

Contains proxy-groups for most regions (**Hong Kong, Taiwan, Japan, Singapore, the United States, South Korea, the United Kingdom, Germany, France, the Netherlands, European manual, European automatic**) and **load balancing** strategies for most regions (**Hong Kong, Taiwan, Japan, Hong Kong, Taiwan and Japan combination, South Korea, Singapore, the United States, unpopular region combination**). The load balancing includes **round robin** (`all requests will be assigned to different proxy nodes in the policy group`) and **hashing** (`assign requests with the same target address to the same proxy node in the policy group`). Please refer to [Kernel configuration](https://wiki.metacubex.one/config/proxy-groups/load-balance/).

# Introduction

## Note:

In the above configuration, external access control [control panel](https://github.com/Zephyruso/zashboard) is enabled by default and the password is set to *"123456789"*. If necessary, please change the password by yourself and modify the secret field in the configuration:

```yaml
secret: 123456789
```

Web control panel **access address**: http://127.0.0.1:9090/ui/zashboard/. If necessary, you can change the port by yourself and modify the external-controller field in the configuration:

```yaml
external-controller: 127.0.0.1:9090
```

## Some enhanced settings:

- Domain name filtering of fake-ip
- DNS mapping of some domain names

------

Thanks to the authors who provided rule sets and tutorials. This project is just for reference and organization.

[@SukkaW](https://github.com/sukkaw)

[@blackmatrix7](https://github.com/blackmatrix7)

[@Zephyruso](https://github.com/Zephyruso)

[@Koolson](https://github.com/Koolson)

Other authors
