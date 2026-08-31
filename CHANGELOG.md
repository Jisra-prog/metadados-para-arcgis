# Changelog

## 1.2.1 — estável

- Corrige a ausência da Faixa de Escala no XML quando o usuário informa somente a escala de referência.
- Restaura a janela de escala simples da versão 1.1.
- Uma única escala confirmada pelo usuário passa a alimentar:
  - escala equivalente/de referência (`rfDenom`);
  - máximo da faixa ArcGIS (`maxScale`);
  - mínimo da faixa ArcGIS (`minScale`).
- Mantém a possibilidade de exportar sem escala.
- Mantém nome, identidade institucional, melhorias visuais e normalização de idioma da v1.2.
- Adiciona os autores:
  - Jorge Jisra;
  - Andresa Dornelas de Castro.
- Mantém a identificação institucional MIDR / Departamento de Obras Hídricas / SNSH.
- Versão validada no QGIS 3.44.13 e no ArcGIS Pro.
- Marcada como estável para publicação (`experimental=False`).

## 1.2.0

- Nome público alterado para **Metadados para ArcGIS**.
- Incluída identificação institucional.
- Melhorias de interface e normalização de idioma.
- Introduzida separação de faixa de escala, posteriormente simplificada na v1.2.1 após teste no ArcGIS.

## 1.1.0

- Janela simples de confirmação de escala.
- Escala de referência enviada ao ArcGIS.
- Possibilidade de exportar sem escala.
