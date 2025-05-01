# ProxyConfig

基于模块化，可以按照如下顺序，自行组合搭配，根据需求删减配置

1. BasicSettings.yaml
2. dns.yaml
3. proxy-groups.yaml
4. rules.yaml
5. rule-providers.yaml
6. proxy-providers.yaml(若使用客户端软件，可省略此模块，例如使用 [sub-store](https://github.com/sub-store-org/Sub-Store))



# 以下给出一些示例：

配置拥有较为完备的内核基础设置和完善的DNS分流设置，proxy-groups 部分拥有较为完善的软件分流，rules 与 rule-providers 部分参考 [作者Sukka](https://github.com/sukkaw) 的设计。

以下配置只有 proxy-groups 部分不同，其余部分未做改动，根据个人需求，在此之上自行修改：

## mihomo.yaml

包含常见地区(**香港、台湾、日本、新加坡、美国、韩国**)的 proxy-groups

##　mihomoPlus.yaml

包含大部分地区(**香港、台湾、日本、新加坡、美国、韩国、英国、德国、法国、荷兰、欧洲手动、欧洲自动**)的 proxy-groups

## mihomoPro.yaml

包含大部分地区(**香港、台湾、日本、新加坡、美国、韩国、英国、德国、法国、荷兰、欧洲手动、欧洲自动**)的 proxy-groups 以及部分地区的**负载均衡**策略(**香港、台湾、日本以及港台日组合**)，其中的负载均衡包括**轮询**(`将会把所有的请求分配给策略组内不同的代理节点`)和**散列**(`将相同的目标地址的请求分配给策略组内的同一个代理节点`)两种，参考 [内核配置](https://wiki.metacubex.one/config/proxy-groups/load-balance/)。

## mihomoProMax.yaml

包含大部分地区(**香港、台湾、日本、新加坡、美国、韩国、英国、德国、法国、荷兰、欧洲手动、欧洲自动**)的 proxy-groups 以及大部分部分地区的**负载均衡**策略(**香港、台湾、日本、港台日组合、韩国、新加坡、美国、冷门地区组合**)，其中的负载均衡包括**轮询**(`将会把所有的请求分配给策略组内不同的代理节点`)和**散列**(`将相同的目标地址的请求分配给策略组内的同一个代理节点`)两种，参考 [内核配置](https://wiki.metacubex.one/config/proxy-groups/load-balance/)。