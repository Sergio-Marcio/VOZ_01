# Mari Presenter MVP

Mari Presenter é um assistente de apresentações controlado por voz, permitindo controlar slides do PowerPoint ou Google Slides sem o uso das mãos.

## Funcionalidades

- **Palavra de Ativação**: "Mari"
- **Comandos de Navegação**:
    - "Próximo", "Avança", "Seguinte" -> Avança o slide
    - "Retorne", "Volta", "Anterior" -> Volta o slide
    - "Slide [número]" -> Pula para um slide específico (ex: "Mari slide 5")
- **Encerramento**: "Encerrar" ou "Sair"

## Pré-requisitos

- Python 3.9+
- Microfone funcional
- Conexão com a internet (para reconhecimento de voz do Google)

## Instalação

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

   *Nota: Se tiver problemas com o PyAudio no Windows, você pode precisar instalar via pipwin ou baixar o wheel apropriado.*

## Uso

1. Abra sua apresentação (PowerPoint ou Google Slides) e coloque em modo de apresentação.
2. Execute o script:
   ```bash
   python main.py
   ```
3. Aguarde a mensagem "Mari está ouvindo!".
4. Diga "Mari próximo" para testar.

## Solução de Problemas

- **Erro PyAudio**: Se falhar na instalação do PyAudio, tente:
  ```bash
  pip install pipwin
  pipwin install pyaudio
  ```
- **Microfone não detectado**: Verifique se o microfone está definido como padrão no sistema.

## Criando o Executável

Para criar um arquivo `.exe` standalone:

1. Instale o PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Gere o executável:
   ```bash
   pyinstaller --onefile --name "MariPresenter" main.py
   ```

3. O executável estará na pasta `dist/`.

