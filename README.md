# IPv6 DDNS仓库

简中|[EN](./README_EN.md)

## 介绍
现在IPv6越来越普及了，用IPv6去访问远程桌面，NAS，Homeassistant这样的服务真的很方便，但是运营上给的IPv6地址不是固定的，经常会变动。

所以如果我们能够写一个小程序，在主机上运行，获取IPv6地址，然后使用域名服务商们的API去更新域名的AAAA记录，那么我们就可以通过域名去访问我们的服务了。

这样就可以极大的方便我们的使用。

## To-do list
- [x] 获取IPv6地址并存入变量
- [ ] 获取域名服务商的API
- [ ] 一个能用的GUI