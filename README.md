# Metadados para ArcGIS — v1.2.1

Complemento para **QGIS 3.44.x** que exporta metadados de camadas QGIS para XML compatível com ArcGIS e converte XML **ISO 19139 / MGB**.

## Autores

- **Jorge Jisra**
- **Andresa Dornelas de Castro**

## Desenvolvimento institucional

Trabalho desenvolvido no âmbito do **Ministério da Integração e do Desenvolvimento Regional (MIDR)**, no **Departamento de Obras Hídricas**, da **Secretaria Nacional de Segurança Hídrica (SNSH)**.

## Escala — comportamento da v1.2.1

A versão 1.2.1 restaura a janela simples e validada da versão 1.1.

O usuário informa uma única **escala de referência** (por exemplo `50000` para `1:50.000`) ou escolhe continuar sem escala.

Quando uma escala é informada, o plugin grava:

- `dataIdInfo/dataScale/equScale/rfDenom` = escala equivalente/de referência;
- `Esri/scaleRange/maxScale` = mesmo denominador;
- `Esri/scaleRange/minScale` = mesmo denominador.

Isso reproduz o comportamento que foi confirmado no ArcGIS Pro.

A ausência de escala **não impede a exportação**.

A escala atual da tela do QGIS é oferecida somente como sugestão e nunca é assumida automaticamente como escala dos dados.

## Funções

- Exportar os metadados da camada ativa do QGIS para XML ArcGIS.
- Converter XML ISO 19139/MGB para XML ArcGIS.
- Preservar, quando disponíveis: título, resumo, descrição, identificador, idioma, datas, palavras-chave, categorias, contatos, créditos, limitações, extensão, temporalidade, CRS, linhagem, distribuição e links.
- Salvar a escala de referência como propriedade personalizada da camada no projeto QGIS.

## Instalação manual

No QGIS:

1. **Complementos → Gerenciar e Instalar Complementos**.
2. **Instalar a partir de ZIP**.
3. Selecione o ZIP instalável desta versão.
4. Clique em **Instalar Complemento**.

## Publicação

Repositório planejado:

`https://github.com/Jisra-prog/metadados-para-arcgis`

Antes do envio ao repositório oficial do QGIS ainda deve ser definido um **e-mail público de contato** no `metadata.txt` e a versão deve ser marcada como estável (`experimental=False`) após os testes finais.

## Licença

GPL-2.0-or-later.
