# ATP Match Winner Prediction Dataset (Pre-Match)

## Descripción general

Este dataset contiene partidos individuales del circuito ATP formulados como un **problema de clasificación binaria pre-match**:

> Dado un partido, predecir qué jugador ganará.

El dataset está pensado como insumo para:
- modelos supervisados de clasificación,
- análisis de variables relevantes en resultados deportivos,
- experimentos con validación temporal en series históricas.

El énfasis del trabajo está puesto en:
- construcción explícita de features,
- procesamiento cronológico,
- eliminación de data leakage,
- trazabilidad de los supuestos utilizados.

---

## Unidad de observación

Cada fila representa **un partido ATP antes de disputarse**.

Características:
- una observación = un partido histórico,
- todas las variables corresponden a información disponible **antes del inicio del partido**,
- no se utilizan estadísticas del partido en curso.

Variable objetivo:
- **y_p1_win** = 1 si el jugador P1 gana
- **y_p1_win** = 0 si el jugador P1 pierde

---

## Fuente de datos original

Los datos provienen del repositorio público:

**Jeff Sackmann – tennis_atp**  
https://github.com/JeffSackmann/tennis_atp

Archivos utilizados:
- Resultados de partidos ATP (`atp_matches_YYYY.csv`)
- Rankings ATP históricos (`atp_rankings_*.csv`)
- Información básica de jugadores (`atp_players.csv`)

No se utilizan:
- datos en vivo,
- cuotas de apuestas,
- APIs externas,
- estadísticas calculadas post-match.

---

## Principio de construcción: Pre-Match y sin Data Leakage

El dataset se construye respetando estrictamente el orden temporal.

Reglas aplicadas:
- los partidos se procesan cronológicamente,
- todas las features se calculan **antes** del partido,
- la información del partido se usa únicamente para actualizar estados futuros.

Este criterio se aplica a:
- ratings Elo,
- estadísticas rolling,
- rachas,
- fatiga,
- head-to-head,
- carga acumulada del torneo.

Ninguna variable utiliza información generada durante el partido que se intenta predecir.

---

## Simetría entre jugadores

Para evitar sesgos estructurales en el target:

- en cada partido se intercambian aleatoriamente los jugadores:
  - con probabilidad 0.5, P1 es el ganador real,
  - con probabilidad 0.5, P1 es el perdedor real.

Consecuencias:
- el target queda aproximadamente balanceado,
- se evita que el modelo aprenda reglas artificiales basadas en el orden de los jugadores.

Todas las variables numéricas se expresan como **diferencias P1 − P2**.

---

## Supuestos generales

- El resultado de un partido puede aproximarse a partir de información histórica previa.
- La superficie es un factor determinante y debe modelarse explícitamente.
- El rendimiento reciente aporta más información que el histórico lejano.
- Rankings faltantes se tratan como información ausente, no como valores neutros.

---

## Grupos de variables

### 1. Habilidad (Elo)

Se utiliza un sistema Elo adaptado al tenis:

- Elo global por jugador.
- Elo específico por superficie (hard / clay / grass).
- Factor K dependiente del nivel del torneo.
- Decaimiento del rating por inactividad prolongada.

El Elo se actualiza **solo después** de cada partido.

---

### 2. Ranking ATP

Se incluyen rankings históricos para capturar información institucional del circuito.

Variables:
- ranking actual,
- puntos ATP,
- variación de ranking y puntos en ventanas de 4 y 8 semanas.

Los rankings faltantes se imputan con valores altos para reflejar baja jerarquía competitiva.

---

### 3. Forma reciente

Se mide la forma mediante resultados previos:

- winrate en los últimos 10 partidos,
- winrate en los últimos 20 partidos,
- racha actual de victorias o derrotas.

---

### 4. Fatiga

Se incluyen indicadores de carga física reciente:

- días de descanso desde el último partido,
- número de partidos jugados en los últimos 7, 14 y 30 días.

---

### 5. Carga del torneo actual

Para cada jugador dentro del torneo en curso:

- partidos jugados previamente,
- minutos acumulados en cancha.

Estas variables permiten modelar desgaste dentro del mismo torneo.

---

### 6. Head-to-Head (H2H)

Se considera el historial previo entre ambos jugadores:

- balance total de enfrentamientos,
- balance específico por superficie.

Ambas métricas se calculan únicamente con partidos anteriores.

---

### 7. Estadísticas históricas de juego

Se calculan promedios móviles (últimos N partidos previos) de:

- tasa de aces,
- tasa de dobles faltas,
- porcentaje de primeros saques dentro,
- porcentaje de puntos ganados con primer saque,
- porcentaje de puntos ganados con segundo saque,
- porcentaje de break points salvados.

Estas estadísticas definen el perfil de juego histórico del jugador.

---

## Tabla de features

| Grupo | Feature | Descripción |
|-----|--------|-------------|
| Elo | elo_diff | Diferencia de Elo global (P1 − P2) |
| Elo | surface_elo_diff | Diferencia de Elo en la superficie |
| Ranking | rank_diff | Diferencia de ranking ATP |
| Ranking | rank_points_diff | Diferencia de puntos ATP |
| Ranking | rank_d4_diff | Cambio de ranking en 4 semanas |
| Ranking | rank_d8_diff | Cambio de ranking en 8 semanas |
| Forma | wr10_diff | Diferencia de winrate últimos 10 partidos |
| Forma | wr20_diff | Diferencia de winrate últimos 20 partidos |
| Forma | streak_diff | Diferencia de racha actual |
| Fatiga | rest_diff | Diferencia de días de descanso |
| Fatiga | m7_diff | Diferencia de partidos últimos 7 días |
| Fatiga | m14_diff | Diferencia de partidos últimos 14 días |
| Fatiga | m30_diff | Diferencia de partidos últimos 30 días |
| Torneo | tourney_matches_so_far_diff | Diferencia de partidos jugados en el torneo |
| Torneo | tourney_minutes_so_far_diff | Diferencia de minutos acumulados |
| H2H | h2h_diff | Diferencia de head-to-head total |
| H2H | h2h_surface_diff | Diferencia de head-to-head en la superficie |
| Stats | ace_rate_diff | Diferencia de tasa de aces |
| Stats | df_rate_diff | Diferencia de tasa de dobles faltas |
| Stats | first_in_rate_diff | Diferencia de primeros saques dentro |
| Stats | first_won_rate_diff | Diferencia de puntos ganados con primer saque |
| Stats | second_won_rate_diff | Diferencia de puntos ganados con segundo saque |
| Stats | bp_saved_rate_diff | Diferencia de break points salvados |

---

## Variables categóricas

Se incluyen como contexto del partido:
- superficie,
- ronda,
- nivel del torneo,
- tipo de entrada (qualy, wildcard, etc.),
- partidos al mejor de 3 o 5 sets.

---

## Qué no incluye el dataset

No se incluye:
- estadísticas del partido actual,
- cuotas de apuestas,
- información médica o lesiones,
- condiciones climáticas,
- información no observable pre-match.

---

## Uso esperado

El dataset está pensado para:
- clasificación binaria supervisada,
- validación temporal (train en años pasados, test en años recientes),
- análisis de importancia de variables,
- comparación de modelos predictivos.

No está diseñado para:
- apuestas deportivas,
- inferencia causal,
- predicción en tiempo real.

---

## Notas finales

Todas las decisiones de construcción del dataset están orientadas a:
- coherencia temporal,
- reproducibilidad,
- claridad en los supuestos,
- separación estricta entre información pre y post match.










---

# ATP Match Winner Prediction Dataset (Pre-Match)

## ¿Qué es este dataset?

Este dataset contiene **partidos individuales del circuito ATP** de tenis, preparados como un **problema de clasificación binaria pre-match**:

> Dado un partido, predecir qué jugador gana.

La idea no es predecir en vivo ni apostar, sino construir un dataset **limpio, realista y temporalmente consistente**, que sirva para:

* entrenar modelos de machine learning,
* analizar qué factores influyen en los resultados,
* hacer validaciones históricas sin data leakage.

El foco principal está en **cómo se construyen las variables**, más que en el modelo final.

---

## Unidad de observación

Cada fila representa **un partido ATP justo antes de jugarse**.

* Una fila = un partido histórico
* Todas las variables usan solo información disponible antes del partido
* No hay estadísticas del partido actual

Variable objetivo:

* `y_p1_win = 1` → gana el jugador P1
* `y_p1_win = 0` → pierde el jugador P1

---

## Fuente de datos

Los datos provienen exclusivamente del repositorio público:

**Jeff Sackmann – tennis_atp**
[https://github.com/JeffSackmann/tennis_atp](https://github.com/JeffSackmann/tennis_atp)

Se usan:

* partidos ATP (`atp_matches_YYYY.csv`)
* rankings ATP históricos
* información básica de jugadores

No se usan:

* cuotas de apuestas,
* datos en vivo,
* APIs externas,
* estadísticas post-match.

---

## Cómo se construye el dataset (y por qué no hay leakage)

Los partidos se procesan **en orden cronológico**.

Para cada partido:

1. Se calculan todas las features usando solo información pasada.
2. Se guarda la fila del dataset.
3. Recién después se actualizan estados internos (Elo, estadísticas, etc.).

Esto aplica a:

* Elo
* forma reciente
* fatiga
* head-to-head
* carga del torneo

Ninguna variable “ve el futuro”.

---

## Orden de jugadores y balance del target

Para evitar sesgos artificiales:

* En cada partido se hace un **swap aleatorio** de jugadores.
* Con probabilidad 0.5, P1 es el ganador real.
* Con probabilidad 0.5, P1 es el perdedor real.

Así:

* el target queda balanceado,
* el modelo no aprende reglas del tipo “el jugador de arriba gana”.

Todas las variables numéricas se expresan como **P1 − P2**.

---

## Supuestos generales

* El resultado de un partido puede aproximarse usando historial previo.
* La superficie importa y se modela explícitamente.
* El rendimiento reciente pesa más que el muy antiguo.
* Rankings faltantes no se “inventan”: se tratan como información ausente.

---

## Variables incluidas

### 1. Habilidad (Elo)

Sistema Elo adaptado al tenis:

* Elo global
* Elo por superficie (hard / clay / grass)
* Factor K dependiente del nivel del torneo
* Decaimiento por inactividad

El Elo **solo se actualiza después** de cada partido.

---

### 2. Ranking ATP

Se incluyen rankings históricos para capturar jerarquía competitiva.

Variables:

* ranking actual
* puntos ATP
* cambios de ranking y puntos en 4 y 8 semanas

Rankings faltantes se imputan con valores altos (baja jerarquía).

---

### 3. Forma reciente

Se mide usando resultados previos:

* winrate últimos 10 partidos
* winrate últimos 20 partidos
* racha actual

---

### 4. Fatiga

Indicadores de carga física:

* días de descanso desde el último partido
* partidos jugados en los últimos 7, 14 y 30 días

---

### 5. Carga del torneo actual

Para el torneo en curso:

* partidos ya jugados
* minutos acumulados en cancha

Esto captura desgaste dentro del mismo torneo.

---

### 6. Head-to-Head

Historial previo entre los jugadores:

* enfrentamientos totales
* enfrentamientos en la misma superficie

Solo se usan partidos anteriores.

---

### 7. Estadísticas históricas de juego

Promedios móviles de partidos previos:

* aces
* dobles faltas
* primeros saques dentro
* puntos ganados con primer saque
* puntos ganados con segundo saque
* break points salvados

Definen el perfil histórico de cada jugador.

---

## Tabla de features principales

| Grupo   | Feature                     | Descripción                        |
| ------- | --------------------------- | ---------------------------------- |
| Elo     | elo_diff                    | Diferencia de Elo global           |
| Elo     | surface_elo_diff            | Diferencia de Elo en la superficie |
| Ranking | rank_diff                   | Diferencia de ranking ATP          |
| Ranking | rank_points_diff            | Diferencia de puntos ATP           |
| Ranking | rank_d4_diff                | Cambio de ranking (4 semanas)      |
| Ranking | rank_d8_diff                | Cambio de ranking (8 semanas)      |
| Forma   | wr10_diff                   | Winrate últimos 10                 |
| Forma   | wr20_diff                   | Winrate últimos 20                 |
| Forma   | streak_diff                 | Racha actual                       |
| Fatiga  | rest_diff                   | Días de descanso                   |
| Fatiga  | m7_diff                     | Partidos últimos 7 días            |
| Fatiga  | m14_diff                    | Partidos últimos 14 días           |
| Fatiga  | m30_diff                    | Partidos últimos 30 días           |
| Torneo  | tourney_matches_so_far_diff | Partidos jugados en el torneo      |
| Torneo  | tourney_minutes_so_far_diff | Minutos acumulados                 |
| H2H     | h2h_diff                    | Head-to-head total                 |
| H2H     | h2h_surface_diff            | Head-to-head por superficie        |
| Stats   | ace_rate_diff               | Tasa de aces                       |
| Stats   | df_rate_diff                | Tasa de dobles faltas              |
| Stats   | first_in_rate_diff          | Primer saque dentro                |
| Stats   | first_won_rate_diff         | Puntos ganados con primer saque    |
| Stats   | second_won_rate_diff        | Puntos ganados con segundo saque   |
| Stats   | bp_saved_rate_diff          | Break points salvados              |

---

## Variables categóricas

Se incluyen como contexto:

* superficie
* ronda
* nivel del torneo
* tipo de entrada (Q, WC, LL, etc.)
* formato del partido (BO3 / BO5)

---

## Uso esperado

Pensado para:

* clasificación supervisada,
* validación temporal,
* análisis de features,
* comparación de modelos.

---


