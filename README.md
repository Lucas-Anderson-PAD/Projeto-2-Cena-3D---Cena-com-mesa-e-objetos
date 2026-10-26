# Projeto-2-Cena-3D---Cena-com-mesa-e-objetos

Projeto 2 – Cena 3D: Mesa e Objetos INF1761 – Computação Gráfica
Nome: Lucas Anderson PAcheco Amora Delphino
Escolhi a Opção 1 (cena com mesa e objetos). E Usei o grafo de cena da disciplina reaproveitando a logica dos códigos das tarefas anteriores (Node, Transform, Shader, Pipeline, Camera3D com Arcball, Cube, Sphere, Light e PhongMaterial). Nada do código base do grafo de cena foi alterado
Aplicação básica
main_mesa.py monta a cena. Cria a câmera com arcball, o shader, o pipeline, os materiais, as texturas e o grafo de cena. A mesa são 5 instâncias do mesmo Cube, escaladas (tampo e 4 pernas), filhas de um nó que passa o material e a textura de madeira para todas. O chão é um Cube achatado, e a esfera e o cubo ficam sobre o tampo.
spotlight.py define a classe SpotLight, derivada de Light, com posição, direção e cone (ângulos interno e externo, guardados como cossenos para o shader). O método map() transforma a posição como ponto e a direção como vetor, então a luz funciona em qualquer espaço de iluminação.
scene.wgsl faz a iluminação por fragmento (Blinn-Phong) em espaço de mundo. O spot é atenuado com smoothstep entre os cossenos do cone, e o decal multiplica a cor do material.
gen_textures.py gera as imagens da pasta images: wood.png (mesa) e checker.png (chão), que são os dois objetos com decal. A esfera e o cubo usam cor sólida (um texel branco 1x1), pois o enunciado pede mais de um objeto com textura, não todos.
Fog, plano de corte e segunda luz
Os três efeitos ficam no scene.wgsl e são ligados e desligados em main_mesa.py (função apply_effects), que escreve os valores nos campos globais do shader com set_value, cada um com uma tecla.
Fog (tecla F): fog linear. A cor final é misturada com a cor de fundo conforme a distância até a câmera, entre fog_near e fog_far.
Plano de corte (tecla C): a classe ClipPlane. Fragmentos do lado negativo do plano são descartados (discard). Troquei o culling do pipeline para none, de modo que as faces de trás vistas pelo corte são pintadas com uma cor de tampa (amarelo), dando a impressão de objeto sólido.
Segunda luz (tecla L): luz pontual de tom quente, com posição e cores nos campos light2_*. Seus termos difuso e especular são somados aos do spot.
Links:
https://github.com/Lucas-Anderson-PAD/Projeto-2-Cena-3D---Cena-com-mesa-e-objetos.git
https://www.youtube.com/watch?v=Y1DnUlizGFk
