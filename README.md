# ATP Match Winner Prediction Dataset

---

## ¿Qué es este dataset?

Este dataset contiene **partidos individuales del circuito ATP** de tenis, preparados como un **problema de clasificación binaria pre-match**:

> Dado un partido, predecir qué jugador gana.

La idea no es predecir en vivo el resultado de un partido, sino construir un dataset limpio y consistente, que sirva tanto para entrenar modelos de machine learning,ver qué factores influyen en los resultados,

El foco principal está en **cómo se construyen las variables**, más que en el modelo final.

---

Cada fila representa **un partido ATP justo antes de jugarse**.

* Una fila = un partido histórico
* Todas las variables usan solo información disponible antes del partido, ya sea respecto a loa jugadores o al torneo.
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
* información básica de jugadores (`atp_players.csv`)

No se usan:

* Datos de apuestas o predicciones similares
* datos en vivo,
* APIs externas,
* estadísticas generadas despues del partido.

---

## Cómo se construye el dataset

Los partidos se procesan **en orden cronológico**, esto es importante para evitar  data leakage.

Las características estáticas (edad, altura, mano dominante) no generan leakage porque no dependen del resultado del partido.

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

En cada partido se hace un **swap aleatorio** de jugadores, con probabilidad 0.5, P1 es el ganador real, es decir que hay probabilidad  0.5, de que P1 sea el perdedor real.

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

## Tabla de features principales

| Grupo     | Feature                     | Descripción                                 |
|-----------|-----------------------------|---------------------------------------------|
| Target    | y_p1_win                    | 1 si gana P1, 0 si pierde                   |
| Identidad | p1_id / p2_id               | ID de jugadores                             |
| Contexto  | date                        | Fecha del partido                           |
| Contexto  | surface                     | Superficie                                  |
| Contexto  | round                       | Ronda                                       |
| Contexto  | tourney_level               | Nivel del torneo                            |
| Contexto  | best_of                     | Formato BO3 / BO5                           |
| Contexto  | entry_p1 / entry_p2         | Tipo de entrada (Q, WC, LL, etc.)           |
| Jugador   | age_diff                    | Diferencia de edad (años)                   |
| Jugador   | height_diff                 | Diferencia de altura (cm)                   |
| Jugador   | lefty_diff                  | Diferencia mano dominante                   |
| Elo       | elo_diff                    | Diferencia de Elo global                    |
| Elo       | surface_elo_diff            | Diferencia de Elo en la superficie          |
| Ranking   | rank_diff                   | Diferencia ranking ATP                      |
| Ranking   | rank_points_diff            | Diferencia puntos ATP                       |
| Ranking   | rank_d4_diff                | Cambio ranking 4 semanas                    |
| Ranking   | rank_points_d4_diff         | Cambio puntos 4 semanas                     |
| Ranking   | rank_d8_diff                | Cambio ranking 8 semanas                    |
| Ranking   | rank_points_d8_diff         | Cambio puntos 8 semanas                     |
| Forma     | wr10_diff                   | Winrate últimos 10 partidos                 |
| Forma     | wr20_diff                   | Winrate últimos 20 partidos                 |
| Forma     | streak_diff                 | Diferencia de racha actual                  |
| Fatiga    | rest_diff                   | Diferencia días de descanso                 |
| Fatiga    | m7_diff                     | Diferencia partidos últimos 7 días          |
| Fatiga    | m14_diff                    | Diferencia partidos últimos 14 días         |
| Fatiga    | m30_diff                    | Diferencia partidos últimos 30 días         |
| Torneo    | tourney_matches_so_far_diff | Diferencia partidos jugados en el torneo    |
| Torneo    | tourney_minutes_so_far_diff | Diferencia minutos acumulados en el torneo  |
| H2H       | h2h_diff                    | Historial total entre jugadores             |
| H2H       | h2h_surface_diff            | Historial en la misma superficie            |
| Stats     | ace_rate_diff               | Diferencia tasa de aces                     |
| Stats     | df_rate_diff                | Diferencia tasa de dobles faltas            |
| Stats     | first_in_rate_diff          | Diferencia primer saque dentro              |
| Stats     | first_won_rate_diff         | Diferencia puntos ganados con primer saque  |
| Stats     | second_won_rate_diff        | Diferencia puntos ganados con segundo saque |
| Stats     | bp_saved_rate_diff          | Diferencia break points salvados            |

---

## Definiciones y valores posibles

| Variable            | Valores posibles                               | Definición                                     |
|---------------------|------------------------------------------------|------------------------------------------------|
| y_p1_win            | 0 / 1                                          | 1 si gana P1, 0 si pierde                      |
| surface             | Hard / Clay / Grass / Carpet / Unknown         | Superficie del partido                         |
| round               | R128, R64, R32, R16, QF, SF, F, RR, Q1, Q2, Q3 | Ronda del torneo                               |
| tourney_level       | G, M, A, C, D, F, etc.                         | Nivel del torneo según ATP                     |
| best_of             | 3 / 5                                          | Formato del partido (sets)                     |
| entry_p1 / entry_p2 | Q, WC, LL, SE, PR, None                        | Tipo de entrada al torneo                      |
| lefty_diff          | -1 / 0 / 1                                     | Diferencia mano dominante (zurdo=1, diestro=0) |
| p1_lefty / p2_lefty | 0 / 1                                          | 1 si zurdo, 0 si diestro                       |

---

## Uso esperado

Pensado para:

* clasificación supervisada,
* validación temporal,
* análisis de features,
* comparación de modelos.

---


