---
name: discovery-mcp-scanner
description: ''
version: 1.0.0
license: MIT
compatibility: opencode
model_role: primary
allowed_tools:
- ls
- mapper
- report
- mcp_slm_remember
tier: 2
---
# Discovery MCP Scanner Skill (discovery-mcp-scanner)

## Overview

Bu skill, harici MCP sunucularını tarayarak onların sunduğu tüm yetenekleri/araçları dinamik olarak keşfeder ve sistemin `ToolBridge` altyapısına güvenli bir namespace prefix (`{server_name}_{tool_name}`) ile kaydeder.

## Architecture Principles

1. **Dynamic Registration**: Sisteme yeni bir MCP sunucusu entegre edildiğinde, kod üzerinde hiçbir değişiklik yapmadan `mcp_config.json` içerisine eklenmesi yeterlidir. Tarayıcı motoru ilk açılışta sunucuyu keşfedip araçları kaydeder.

2. **Namespace Isolation**: Çakışmaları engellemek için tüm araçlar `{sunucu_adi}_{arac_adi}` şablonuyla izole edilir.

3. **Execution Safety**: Keşfedilen tüm araçlar, `ToolBridge._dispatch` üzerinden standard RBAC, telemetry ve VRAM hygiene (temizlik) kontrollerine tabi tutulur.

## Kullanım Rehberi

Yeni bir MCP sunucusu eklemek için:

1. `mcp_config.json` dosyasını güncelleyin veya çevre değişkenlerini tanımlayın.

2. Sunucu araçları ilk tetikleme anında dinamik olarak `ToolBridge` sınıfına kaydedilecek ve `_dispatch` üzerinden doğrudan çağrılabilir olacaktır.
