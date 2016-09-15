#!/usr/bin/env Rscript

# Once upon a time with was an attmpt to crack the mod power formula, I got
# bored in the middle so it was never finished.

# multi domain function
#   0.5*pwr + 0.5,                     for pwr E N and      pwr < 7
#   2.775306*pwr^(1/3) - 1.044751,     for pwr E N and 7 <= pwr < 1046
#   11.1759954*pwr^(1/8) + 0.5029773,  for pwr E N and      pwr >= 1046

# finding that I am dealing with more than one function
mod <- read.table("mod-power", header=TRUE)
x <- mod$pwr
dfx <- data.frame(x=x,
		  diff.x=c(diff(x),NA),
		  d.d.x=c(diff(diff(x)),NA,NA),
		  d.d.d.x=c(diff(diff(diff(x))),NA,NA,NA),
		  d.d.d.d.x=c(diff(diff(diff(diff(x)))),NA,NA,NA,NA))
#plot(plot(mod$pwr, mod$modpwr)
#plot(mod$pwr^(1/3), mod$modpwr)
#plot(mod$pwr[27:35]^(1/3), mod$modpwr[27:35])
#plot(mod$pwr[1:26]^(1/3), mod$modpwr[1:26])
#plot(mod$pwr[1:3], mod$modpwr[1:3])
#plot(mod$pwr[4:26]^(1/3), mod$modpwr[4:26])

f0 <- mod[1:3,]
f1 <- mod[4:26,]
f2 <- mod[27:35,]
f0coef <- glm(f0$modpwr ~ f0$pwr)$coef           # ^1 gives the best intercept
f1coef <- glm(f1$modpwr ~ I(f1$pwr^(1/3)))$coef  # ^3, best intercept
f2coef <- glm(f2$modpwr ~ I(f2$pwr^(1/8)))$coef  # ^8, best intercept

f0res <- (f0coef[[2]])*f0$pwr + f0coef[[1]]
f1res <- (f1coef[[2]])*(f1$pwr^(1/3)) + f1coef[[1]]
f2res <- (f2coef[[2]])*(f2$pwr^(1/8)) + f2coef[[1]]
modfull <- cbind(mod$pwr, mod$modpwr, c(f0res,f1res,f2res))

plot(mod$pwr, mod$modpwr)
points(f0$pwr, round(f0res), pch="+", col="red")
points(f1$pwr, round(f1res), pch="+", col="blue")
points(f2$pwr, round(f2res), pch="+", col="green")

