[English](https://github.com/Yronos/ProxyConfig/blob/main/README.md) | [中文](https://github.com/Yronos/ProxyConfig/blob/main/README_zh.md)
# ProxyConfig

基于模块化，可以按照如下顺序，自行组合搭配，根据需求删减配置

1. BasicSettings.yaml
2. dns.yaml
3. proxy-groups.yaml
4. rules.yaml
5. rule-providers.yaml
6. proxy-providers.yaml(若使用客户端软件，可省略此模块，例如使用 [sub-store](https://github.com/sub-store-org/Sub-Store))



# 快速使用：

配置拥有较为完备的内核基础设置和完善的DNS分流设置，proxy-groups 部分拥有较为完善的软件分流，rules 与 rule-providers 部分参考 [作者Sukka](https://github.com/sukkaw) 的设计。

以下配置只有 proxy-groups 部分不同，其余部分未做改动，根据个人需求，在此之上自行修改：

## config.yaml

包含常见地区(**香港、台湾、日本、新加坡、美国、韩国**)的 proxy-groups

##　configPlus.yaml

包含大部分地区(**香港、台湾、日本、新加坡、美国、韩国、英国、德国、法国、荷兰、欧洲手动、欧洲自动**)的 proxy-groups

## configPro.yaml

包含大部分地区(**香港、台湾、日本、新加坡、美国、韩国、英国、德国、法国、荷兰、欧洲手动、欧洲自动**)的 proxy-groups 以及部分地区的**负载均衡**策略(**香港、台湾、日本以及港台日组合**)，其中的负载均衡包括**轮询**(`将会把所有的请求分配给策略组内不同的代理节点`)和**散列**(`将相同的目标地址的请求分配给策略组内的同一个代理节点`)两种，参考 [内核配置](https://wiki.metacubex.one/config/proxy-groups/load-balance/)。

## configProMax.yaml

包含大部分地区(**香港、台湾、日本、新加坡、美国、韩国、英国、德国、法国、荷兰、欧洲手动、欧洲自动**)的 proxy-groups 以及大部分部分地区的**负载均衡**策略(**香港、台湾、日本、港台日组合、韩国、新加坡、美国、冷门地区组合**)，其中的负载均衡包括**轮询**(`将会把所有的请求分配给策略组内不同的代理节点`)和**散列**(`将相同的目标地址的请求分配给策略组内的同一个代理节点`)两种，参考 [内核配置](https://wiki.metacubex.one/config/proxy-groups/load-balance/)。



# 介绍

## 注意：

以上配置中都默认开启了外部访问控制 [控制面板](https://github.com/Zephyruso/zashboard) 且密码设置为了*“123456789”*，如有需要请自行更改密码，修改配置中的 secret 字段：

```yaml
secret: 123456789
```

网页端控制面板**访问地址**：http://127.0.0.1:9090/ui/zashboard/，如有需要可自行更改端口，修改配置中的 external-controller 字段：

```yaml
external-controller: 127.0.0.1:9090
```

## 部分增强设置：

- fake-ip 的域名过滤
- 部分域名的DNS映射

------

在此感谢提供规则集与教程的各位作者，该项目只是借鉴使用与整理工作。

[@SukkaW](https://github.com/sukkaw)

[@blackmatrix7](https://github.com/blackmatrix7)

[@Zephyruso](https://github.com/Zephyruso)

[@Koolson](https://github.com/Koolson)

等作者