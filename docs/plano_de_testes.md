# Plano de testes

Os testes do jogo são manuais: aspectos visuais, sensação de controle, áudio e o fluxo
completo entre as telas são verificados jogando, seguindo o roteiro abaixo.

## Roteiro de testes manuais

| # | Passo | Resultado esperado |
|---|---|---|
| 1 | `python main.py` | Abre o menu com título, esferas e dragão animado |
| 2 | Setas ↑/↓ e mouse sobre as opções | Seleção muda, com som e cursor de esferas girando |
| 3 | Abrir "Instruções" e voltar com ESC | Tela de instruções legível; volta ao menu |
| 4 | "Jogar" e mover com setas e WASD | Dragão se move suavemente, cabeça gira nas curvas |
| 5 | Tentar inverter direção (ex.: → e depois ←) | Comando ignorado, sem morte |
| 6 | Seguir o radar até a esfera | Câmera acompanha; esfera coletada com partículas, anel, "+pontos", som, HUD atualizado |
| 7 | Observar após a coleta | Faixa "NÍVEL N", rochas novas surgindo com animação, velocidade maior, céu mudando de cor |
| 8 | Segurar ESPAÇO | Aura azul, barra de Ki diminuindo e piscando, dragão mais rápido |
| 9 | ESC durante o jogo | Painel de pausa; HUD mostra "PAUSADO"; o jogo fica congelado |
| 10 | ESC novamente | Partida continua exatamente de onde parou |
| 11 | Colidir com rocha, corpo e barreira (em partidas diferentes) | Tremor, desintegração do dragão, painel com o motivo correto |
| 12 | R ou "Jogar novamente" | Nova partida limpa (pontos 0, 1ª esfera) |
| 13 | Coletar as 7 esferas | Cinemática: escurecimento, relâmpagos, esferas voando do HUD, feixe de luz, clarão, Shenlong gigante, painel de vitória |
| 14 | ENTER durante a cinemática | Pula direto para o painel. Segurar ESPAÇO não pula nada |
| 15 | Fechar a janela em qualquer tela | Programa encerra sem erro |
| 16 | Alt+Tab durante a partida | O jogo pausa automaticamente |
| 17 | Apagar `save/highscore.json` e jogar | Recorde recomeça em 0 sem erro |

## Desempenho

Medição sem janela (driver dummy) no fim de jogo, com dragão de 22 segmentos, 26 rochas e
mais de 1300 partículas simultâneas: **≈15 ms por quadro** (atualização + desenho), dentro do
orçamento de 16,7 ms para 60 FPS. Em jogo normal o número de partículas é bem menor.
