#!/usr/bin/env Rscript

level <- function(max_level, base_cost, level_cost, exponent) {
  vec <- seq(0, max_level-1)
  round((vec*level_cost + base_cost)**(1 + exponent*vec))
}

costs <-
list(misc_posting     = c(  20,  5000,   100, 0.0280232009 ) ,
     adept_learner    = c( 300,   100,    50, 0.000417446  ) ,
     assimilator      = c(  10, 50000, 50000, 0.0058690916 ) ,
     ability_boost    = c( 500,   100,   100, 0.0005548607 ) ,
     power_tank       = c(  20,  2000,  1000, 0            ) ,
     scavenger        = c(  50,   500,   500, 0.0088310825 ) ,
     luck_of_the_draw = c(  25,  2000,  2000, 0.0168750623 ) ,
     quartermaster    = c(  20,  5000,  5000, 0.017883894  ) ,
     archeologist     = c(  10, 25000, 25000, 0.030981982  ) ,
     set_collector    = c(   4, 12500, 12500, 0            ) ,
     pack_rat         = c(   5, 20000, 20000, 0            ) ,
     refined_aura     = c(   4, 25000, 25000, 0            ) )

prices <- lapply(costs, function(x){ level(x[1], x[2], x[3], x[4]) })
print(prices)

