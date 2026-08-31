# Guia simples — instalar, testar e publicar

## 1. Instalar o ZIP no seu QGIS

1. Abra o QGIS.
2. Vá em **Complementos > Gerenciar e Instalar Complementos**.
3. Abra a opção **Instalar a partir de ZIP**.
4. Escolha o arquivo `qgis_metadata_arcgis_v1.0.0.zip`.
5. Confirme a instalação.
6. Se aparecer aviso de complemento experimental, permita/exiba complementos experimentais nas configurações do Gerenciador de Complementos enquanto a versão 1.0 estiver em teste.

Depois disso, selecione uma camada. O botão do plugin aparecerá na barra de ferramentas e o menu também ficará disponível em **Complementos > Metadados QGIS → ArcGIS**.

## 2. Testar

Faça pelo menos estes testes:

- camada vetorial com metadados preenchidos;
- camada raster com metadados preenchidos;
- camada sem bounding box de metadados (o plugin usa a extensão real da camada como fallback);
- arquivo ISO 19139 existente;
- abrir o XML final no ArcGIS Pro e conferir os campos.

## 3. Editar o código, se precisar

Você pode usar o **Visual Studio Code**. Os arquivos principais são:

- `plugin.py`: botão, menus e janelas;
- `qgis_reader.py`: leitura dos metadados internos do QGIS;
- `iso19139_reader.py`: leitura de XML ISO 19139;
- `metadata_model.py`: estrutura intermediária;
- `arcgis_writer.py`: criação do XML ArcGIS.

Para mudanças pequenas, o VS Code é suficiente. O Qt Designer só será necessário se no futuro você quiser criar uma janela de configuração mais complexa.

## 4. Publicar o código no GitHub

1. Crie uma conta no GitHub, caso ainda não tenha.
2. Crie um repositório público chamado, por exemplo, `qgis-metadata-arcgis`.
3. Envie para o repositório os arquivos da pasta `qgis_metadata_arcgis`.
4. Não envie apenas o ZIP: o repositório oficial do QGIS exige acesso ao código-fonte público.
5. No `metadata.txt`, substitua `SEU_USUARIO` pelo seu usuário do GitHub e preencha `author` e `email`.

Exemplo, se seu usuário for `joao123`:

```ini
repository=https://github.com/joao123/qgis-metadata-arcgis
homepage=https://github.com/joao123/qgis-metadata-arcgis#readme
tracker=https://github.com/joao123/qgis-metadata-arcgis/issues
```

## 5. Criar conta OSGeo

Para enviar o plugin ao repositório oficial do QGIS você precisa de um **OSGeo ID**.

Depois, entre no site oficial de plugins do QGIS e use a opção de enviar/compartilhar um plugin.

## 6. ZIP correto para publicação

O ZIP deve conter UMA pasta raiz com o plugin, assim:

```text
qgis_metadata_arcgis_v1.0.0.zip
└── qgis_metadata_arcgis/
    ├── __init__.py
    ├── metadata.txt
    ├── plugin.py
    ├── metadata_model.py
    ├── qgis_reader.py
    ├── iso19139_reader.py
    ├── arcgis_writer.py
    ├── icon.png
    ├── LICENSE
    └── README.md
```

## 7. Antes de publicar a primeira versão

- Teste no seu QGIS 3.44.13.
- Teste o XML gerado no ArcGIS Pro.
- Preencha os links reais no `metadata.txt`.
- Troque `experimental=True` para `experimental=False` somente quando considerar a versão estável.
- Aumente a versão toda vez que publicar uma atualização, por exemplo 1.0.1, 1.2.0 etc.

## Nova etapa de escala (v1.2.0)

Ao exportar uma camada diretamente do QGIS, o plugin abre a janela **Escala de referência para o metadado ArcGIS**.

- Se você souber a escala de produção/referência, informe apenas o denominador, por exemplo `50000`, ou use `1:50.000`.
- O botão **Usar escala atual do mapa** copia a escala exibida na tela principal do QGIS. Ela é apenas uma sugestão, pois muda com o zoom.
- Se a escala não for conhecida, selecione **Não informar escala e continuar a exportação**. O XML será criado normalmente.
- A opção **Salvar esta escala para esta camada dentro do projeto QGIS** guarda o valor para a próxima exportação. Salve o projeto QGIS para manter essa propriedade entre sessões.
