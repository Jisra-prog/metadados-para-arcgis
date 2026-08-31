# Checklist para publicação no repositório oficial do QGIS

Situação da versão **1.2.1**:

- [x] Testada no QGIS 3.44.13.
- [x] Faixa de Escala confirmada no ArcGIS Pro.
- [x] E-mail público definido: `Isilvajorge3@gmail.com`.
- [x] `experimental=False` no `metadata.txt`.
- [x] `repository`, `homepage` e `tracker` apontando para o GitHub público.
- [x] ZIP instalável gerado com uma única pasta-raiz `qgis_metadata_arcgis/`.
- [ ] Concluir o manual ilustrado com os prints de todas as abas do QGIS.
- [ ] Confirmar autorização institucional para a identificação MIDR/DOH/SNSH, se necessário internamente.
- [ ] Criar/confirmar o OSGeo ID.
- [ ] Enviar o ZIP estável pelo portal oficial de plugins do QGIS.
- [ ] Aguardar a validação/aprovação do repositório oficial.

## Arquivo para submissão

Use o ZIP estável da versão 1.2.1, cuja estrutura interna começa por:

```text
qgis_metadata_arcgis/
├── __init__.py
├── metadata.txt
├── LICENSE
├── plugin.py
└── ...
```
