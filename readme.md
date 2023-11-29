Authors: IndexError, polychromatic

Hi everyone, so it's me IndexError (or as you know me as a composer or ex-mapper, HowToPlayLN) again. I'm here to talk a bit about the improvement to the skillbans system, which we changed A LOT from 2023, I suppose it's going to fix a lot of issues happening here.
## Flaws from the previous system

This is going to be me dedicating 1 whole topic for roasting myself. Because of how I didn't know that much of anything back then. This is going to be a bit of technical details but I will try my best to explain to you in a more simplified manner.

In the previous system, the feature used is the modified version of the score, which is the logit function of the score:
$$
f(x) = \log\left(\frac{1}{10^6 - x}\right)
$$
After being tested with the current ranked score features, this feature does not tell anything much about the score, which is really difficult to interpret (you may consider them as the way to smooth the score to get the more detailed skill level but that doesn't help)

Next, ETI feature is really sensitive to the missing data, for this I will describe them even more in the next subsection, the standardized score is not the correct way to respond to the missing data, which is sparse (a lot of zeros or missing data). The way of imputing data may increase the inefficiency of the model as tested in the [Medium Article](https://towardsdatascience.com/your-dataset-has-missing-values-do-nothing-10d1633b3727).

The way to obtain ETI feature is also not valid because of the different linear equation parameters, this may create the inconsistencies in our features. The linking ETI between tournaments creates higher inconsistencies in the ETI of the players, not to mention about the multicollinearity (where the scores or ETI are correlated to each other).

The outlier detection tools may even have flaws due to several factors
- The usage of overengineered features that are really difficult to interpret
- The concern on dissymmetry of the distance metric introduced in the Local Outlier Factor
- Usage of the different models (One-Class SVM and LOF), without sufficient knowledge of what they are doing

Upon comparing the model results against the results from manual classification by experienced players, the performance of the model is unsatisfactory, and data leakage (The test and the data used to analyze are the same) also affects the validity of the model. Overall, the methodology was inappropriate to handle skillbans.

One may argue that no model is perfect, but it is better to have something more efficient for this, right?
## So what's new?

We basically threw the old system out of the window and started again! This time we will introduce something that actually the indicator of the skills of a player compared to other players, which is nothing but, ELO. This system was introduced in various sports, or even with the game of chess. The first appearance of ELO indirectly in VSRG was in [QuaverPvM](https://qpvm.icedynamix.moe/) (IceDynamix, 2021) and the first appearance in osu!mania was in [SOFT6](https://osu.ppy.sh/wiki/en/Tournaments/SOFT/6) (SurfChu85 and Albionthegreat, 2022), as they introduced the adjustments to the original ELO system with the qualifier results in a tournament.
## ELO system

Elo (1967) proposed the system for measuring the rating of the players based on the matchup history of the players. This system is trying to measure the expected outcome from the actual outcome. For example, you may consider the player A has $R_A$ rating and player B has $R_B$ rating. You calculate the expected outcomes using the formula:

$$
\begin{gather}
E_A = \frac{1}{1+\exp\left(k(R_B - R_A)\right)}\\
E_B = \frac{1}{1+\exp\left(k(R_A - R_B)\right)}
\end{gather}
$$
Where $k = \ln(10)/400$, and $\exp(x) = e^x$. Then after the match is finished, we obtain the actual outcome for each player (win or lose) which we denoted as $S_A$ and $S_B$, we calculate the rating changes from the match, which is:
$$
\begin{gather}
R_A \leftarrow R_A + t(S_A - E_A)\\
R_B \leftarrow R_B + t(S_B - E_B)
\end{gather}
$$
Where $t$ is any constant.

This may be interpreted as, as the rating is higher, the expectation of the player to win other player is also high, if that player ended up losing, the rating will be decreased more compared to the player with lower rating.
## Skillbans in 2024

### How do we implement ELO?

We need to calculate the winning chances of the player $i$ to the player $j$, denoting as $p_{ij}$, which will be the actual outcome in the competition. We then change the rating update formula to
$$
\begin{gather}
x_i \leftarrow x_i + t(p_{ij} - \hat{p}_{ij})\\
x_j \leftarrow x_j + t(p_{ji} - \hat{p}_{ji})
\end{gather}
$$
Here, we changed the notation a bit, as $R$ was changed to $x$, $E$ was changed to $\hat{p}$ to represent the expected winning probability that player $i$ will win player $j$. This will also be beneficial for the formulation in the other sections.

To obtain each $x_i$, we simulate the competition by first, calculating the winning probability of each player, and then use them to calculate the ELO by following the procedure described above.
### Calculating the winning probability

In this case, we manually select the ranked/loved beatmaps that are sufficient to imitate the tournament mappools, denoted $M$.

Denoting $M_i \subset M$ as maps that player $i$ has played in the selected beatmaps. Define the intersection as
$$
S_{ij} = M_i \cap M_j
$$
Let $m$ be each map in $S_{ij}$ In this particular section $\sum (\cdot)$ refers to
$$
\sum_{m \in S_{ij}} (\cdot)
$$
Let
$$
\text{win}_i(m) = \begin{cases}
1 & \text{if player}_i\text{ wins player}_j\text{ in map } m\\
0 & \text{if player}_i\text{ loses player}_j\text{ in map } m\\
0.5 & \text{if player}_i\text{ draws player}_j\text{ in map } m
\end{cases}
$$
In tournament, winning means that the score of player 1 is greater than the score of player 2, the definition of winning/losing or draw is pretty trivial here. 

However if we use this purely, this may be biased towards some skillsets given the selected maps skillset may be unbalanced. We can actually weight them by using the Ratio of Rice and/or LN of the particular map, so that Rice and LN are weighted (nearly) equally to each other.

This may be a naive way to do it, but there was not more information regarding the beatmaps other than the rice count and LN count in each map, except we are doing manual labelling which is a tedious work. We then define them by
$$
\begin{gather}
\text{rice\_ratio}(m) = \frac{\text{rice notes in map }m}{\text{total notes in map }m}\\
\text{LN\_ratio}(m) = \frac{\text{long notes in map }m}{\text{total notes in map }m}
\end{gather}
$$
We then can calculate the probability of winning given the map is Rice and LN by
$$
\begin{gather}
P(\text{win | Rice}) = \frac{\sum \text{win}_i(m) \cdot \text{rice\_ratio}(m)}{\sum \text{rice\_ratio}(m)}\\
P(\text{win | LN}) = \frac{\sum \text{win}_i(m) \cdot \text{LN\_ratio}(m)}{\sum \text{LN\_ratio}(m)}
\end{gather}
$$
Therefore, probability of winning overall is the average of probability of winning given the map is rice, and the probability of winning given the map is LN.
$$
p_{ij} = \begin{cases}
P(\text{win | Rice}) & \sum \text{LN\_ratio} = 0\\
P(\text{win | LN}) & \sum \text{Rice\_ratio} = 0\\
\left(P(\text{win | Rice}) + P(\text{win | LN})\right) / 2 & \text{otherwise.}
\end{cases}
$$
However, in the code, if there is no map that both players play, the probability will be remarked as `null`, or as a missing data.
### Simulating the Competition

After obtaining the probability of winning, the next procedure is to simulate the competition, to do this we then can use the probability of winning $p_{ij}$ as an expected outcome, then we calculate the actual outcome $\hat{p}_{ij}$ by recalling the formula
$$
\hat{p}_{ij} = \frac{1}{1 + \exp(-k(x_i - x_j))}
$$
Where $x_i - x_j$ is the difference between ELO of player $i$ and player $j$, as well as it is worth mentioning that the sigmoid (or logistic function), having a form of:
$$
f(x) = \frac{1}{1 + \exp(-x)}
$$
This function has a graph that looks like this:

![[Pasted image 20231129162312.png]]

So as the difference of ELO increases, the expected winning probability also increases too. Then we want to fit the expected chance of winning to the actual chance of winning based on the information we have got via ELO. Using the proposed way to update the ELO:
$$
\begin{gather}
x_i \leftarrow x_i + (p_{ij} - \hat{p}_{ij})\\
x_j \leftarrow x_j - (p_{ij} - \hat{p}_{ij})
\end{gather}
$$
We then can obtain the values which will be used for skillbans.

The next section is going to be the interpretation of ELO in the likelihood statistics, which we will prove that ELO is the way to maximize the likelihood of some categorical or parametric distribution.
### Maximum Likelihood

Now we first assume that the actual outcome is categorical (win/loss), we can model ELO as a Bernoulli Distribution. Bernoulli Distribution represents the probability of success or failure of the event, for example, a coin flip can be modelled as Bernoulli Distribution of probability 0.5 (assume head is a success and tail is a failure). The probability of winning in this case is the expected winning rate, which is $\hat{p}_{ij}(x)$ (where $x$ represents the ELO of all players, but we use just player $i$ and $j$ to calculate) in the case of the competition. Therefore we can model the result of player $i$ against player $j$ (assume draws don't exist) as
$$
w_{ij} \sim \text{Bernoulli}(\hat{p})
$$
Where
$$
w_{ij} = \begin{cases}
1 & \text{Player }i\text{ wins Player }j\\
0 & \text{otherwise.}
\end{cases}
$$
Then we can use the Likelihood function to find the ELO of each player
$$
\ell(x) = \sum_{i, j \text{ valid}} \left[w_{ij}\log(\hat{p}_{ij}(x)) + (1-w_{ij})\log(1 - \hat{p}_{ij}(x))\right]
$$
However we need to fix that the average of ELO of all players in this case is $0$for the simplification in analysis.
$$
\sum_{i=1}^{n} x_i = 0
$$
One may include the variation penalty (may introduce it as variance or 2-norm), that if the ELO has too much variations, it may cause inaccuracy or the computations will explode:
$$
\|x\|_2 \leq t
$$
For our case where $w_{ij}$ is represented by $p_{ij}$, probability of winning of player $i$ against player $j$. It is going to be a different distribution, but we can still write the likelihood function in the same form!
$$
\ell(x) = \sum_{i, j \text{ valid}} \left[p_{ij}\log(\hat{p}_{ij}) + (1-p_{ij})\log(1 - \hat{p}_{ij})\right]
$$
The really fun fact is, with some really tedious calculations, we can say that the ELO system is the Stochastic Gradient Ascent (opposite of Gradient Descent) of the MLE optimization problem! One needs to show that the Gradient of the piece in the log-likelihood sum is equal to:
$$
\nabla_{x_i, x_j} \left[p_{ij}\log(\hat{p}_{ij}) + (1-p_{ij})\log(1 - \hat{p}_{ij})\right]= (p_{ij} - \hat{p}_{ij}) \begin{bmatrix}1\\-1
\end{bmatrix}
$$
At first, we tried to maximize the said likelihood using the Frank-Wolfe Method (see Appendix), we found out that the solution we obtained may be inaccurate compared to using the simulation due to the constraint that penalizes the variations is forced in the method. We then stick with the simulation way instead.
### More on Simulation

Continuing from the Simulating the Competition, we also don't want ELO to have a relationship with playcount, or at least we want them to be least sensitive to the number of plays (in the experiment, we found out that ELO is sensitive to playcount). We then propose the weighting to reduce the dependence of ELO on playcount, $\gamma$, where $0 < \gamma < 1$:
$$
x_i \leftarrow x_i + \gamma_i^k(p_{ij} - \hat{p}_{ij})
$$
Where $k$ is the playcount of the player $i$ in the simulation. We then find the maximum number of iterations by defining a tolerance $\epsilon$, being a very small number. Then if the change is less than $\epsilon$, we terminate the iterations.

We denoted changes at iteration $k$ as $\Delta p_k$
$$
|\gamma_{i}^k \Delta p_k + \gamma_{i}^{k+1} \Delta p_{k+1} + \gamma_{i}^{k+2} \Delta p_{k+2} + ...| \leq \gamma_{i}^k |\Delta p_k| + \gamma_{i}^{k+1} |\Delta p_{k+1}| + ...
$$
Then in the extreme case where $p_{ij} = 0; \hat{p}_{ij} = 1$ or $p_{ij} = 1; \hat{p}_{ij} = 0$, then $|\Delta p_k| = 1$. It is obvious that the difference cannot exceed $1$ in the normal case.
$$
\begin{gather}
\gamma_{i}^k |\Delta p_k| + \gamma_{i}^{k+1} |\Delta p_{k+1}| + ... \leq \gamma_{i}^k + \gamma_{i}^{k+1} + \gamma_{i}^{k+2} + ...\\
\leq \gamma_{i}^{k} (1 + \gamma + \gamma^2 + ...) \leq \frac{\gamma_{i}^{k}}{1 - \gamma_i} \leq \epsilon
\end{gather}
$$
Then we get
$$
k \geq \frac{\log (\epsilon (1 - \gamma))}{\log(\gamma)}
$$
We then use $\gamma = 0.9995$ and $\epsilon = 0.01$ for the experiment, which is going to be a minimum of 24402 playcounts according to the formula for each player.
## Experimental Result
### ELO relationships to Dans

An interesting finding is that the ELO we have just derived, has a significant relationship with the skill level of 4 digit players, and this ELO is therefore somewhat reliable in detecting outliers in the 4 digit player population for skillbanning. 

Now, we associate a player's skill level to dans. Dans are widely played by the 4K mania community, and generally serve as an indicator of the physicality of a player, therefore contributes significantly to judging the skill level of a player for this skillban exercise. We list both Rice and LN dans considered for the exercise: 

**Rice Dans**

- Alpha-Dan Reform (α-Dan)
- Luminal v2 (δ-★) 
- Beta-Dan Reform (β-Dan)
- Gamma-Dan Reform (γ-Dan)
- Tachyon v3 (ε-δ)
- Delta-Dan Reform (δ-Dan)
- Epsilon-Dan Reform (ε-Dan)

**LN Dans**

- 11th Dan ~ Yoake ~ (夜明け)', 
- 12th Dan ~ Yuugure ~ (夕暮れ)', 
- 13th Dan ~ Yoru ~ (夜)', 
- LN Tier Alternative (Stigma)
- LN Tier Alternative (Koppa)
- 14th Dan ~ Yami ~ (闇) 
- LN Tier Alternative (Sampi)
- 15th Dan ~ Yume ~ (夢)

We then consider the data from [osu!mania 4k High-Tier Dan Courses Clear List](https://docs.google.com/spreadsheets/d/1PFtjPzDEBMkgnOkOWGpDTf3jkFiFfdkGolQ_7J55Ugo/edit#gid=0) (MashedPotato, 2021) associating them with ELO to create the following diagrams:

![[Pasted image 20231129225213.png]]
![[Pasted image 20231129230701.png]]
The figures above are a box plot and the median of the ELO that we just derived of each player in the following rice dans respectively:

- Alpha-Dan Reform (α-Dan)
- Luminal v2 (δ-★) 
- Beta-Dan Reform (β-Dan)
- Gamma-Dan Reform (γ-Dan)
- Tachyon v3 (ε-δ)
- Delta-Dan Reform (δ-Dan)
- Epsilon-Dan Reform (ε-Dan)

![[Pasted image 20231129225225.png]]
![[Pasted image 20231129230728.png]]

The figures above are a box plot and the median of the ELO that we just derived of each player in the following LN dans respectively:

- 11th Dan ~ Yoake ~ (夜明け)
- 12th Dan ~ Yuugure ~ (夕暮れ)
- 13th Dan ~ Yoru ~ (夜)
- LN Tier Alternative (Stigma)
- LN Tier Alternative (Koppa)
- 14th Dan ~ Yami ~ (闇) 
- LN Tier Alternative (Sampi)
- 15th Dan ~ Yume ~ (夢)

Now, we assume that the distribution of 4 digit players by ELO follows a normal distribution. We particularly interested in the behavior of Gamma players for being the dan that is considered really challenging for 4 digits in the current era. We found out that ELO of average (by median) gamma player is really close to equivalent to having the ELO obtained by top 5% of eligible 4 digit players. ELO for the top 25% of gamma players is really close to equivalent to having the ELO of top 2.5% of eligible 4 digit players. 

### Skillbans

We can conclude that Gamma players, whom lie within the top 2.5% of eligible 4 digit players are outliers relative to the distribution. Therefore, it suffices to skillban players who satisfy the following: 

1. are 4 digit; 
2. signed up for 4dm
3. their ELO lies in the top 2.5% of the normal distribution used to model all 4 digit players, as they are considered to possess the physicality of a gamma player.

### Possible Improvements

- For this particular study, we used ELO rating to measure the skill of the players. However, there is also another rating system called [glicko-2](https://en.wikipedia.org/wiki/Glicko_rating_system) which considers the rating deviation into plays in the algorithm, which may be possible to be implemented further in the skillban studies.
- Currently, the beatmaps selected are still being manually picked. There may be a possible way to automatically select the beatmaps that are suitable for the tournament environment.
### Footnotes

- The code is going to be an open-source. If you are going to use it for your own database or tournament, feel free to do so! We would also really appreciate the improvement regarding the code efficiency and documentation in the current codebase, and feel free to experiment the different ideas as well!
- If you are really particularly interested in expanding, or having this project, please DM me on Discord: indexerror, or my email: lkycst@gmail.com so we can discuss about doing the handover from my part to yours in the future.
## References

SurfChu85 and Albionthegreat, 2022. "The SOFT Tournament System". Available at: https://drive.google.com/file/d/1YeKwnTng_Ptz094doqC0bD6wtZilxAl6/view?usp=sharing

Elo, 1967. "The Proposed USCF Rating System, Its Development, Theory, and Applications" (PDF). Available at: https://uscf1-nyc1.aodhosting.com/CL-AND-CR-ALL/CL-ALL/1967/1967_08.pdf#page=26

IceDynamix, 2021. "QuaverPvM". Available at: https://qpvm.icedynamix.moe/

MashedPotato, 2021. "osu!mania 4K High-Tier/Dan Courses Clear List". Available at: https://docs.google.com/spreadsheets/d/1PFtjPzDEBMkgnOkOWGpDTf3jkFiFfdkGolQ_7J55Ugo/edit#gid=0
## Appendix

### Frank-Wolfe Method

**Frank-Wolfe Method**, is the method to solve the optimization problem:
$$
\begin{gather}
\min f(x)\\
\text{subject to } x \in S 
\end{gather}
$$
Where $S$ is convex. By approximating the function into the linear form using Taylor's Series 1st Order Expansion:
$$
\begin{gather}
\min f(x) + (z - x)^T\nabla_xf(x)\\
\text{subject to } z \in S
\end{gather}
$$
This will become Linear Programming or Second-Order Cone Programming, which is simpler to solve using `cvxpy` module. Then we use the exact line search by considering Frank-Wolfe Solution $z^{(k)}$ and the value at the current iteration $x^{(k)}$:
$$
x^{(k+1)} = (1-t) x^{(k)} + tz^{(k)}
$$
Where $t; 0 \leq t \leq 1$ minimizes $f((1-t) x^{(k)} + tz^{(k)})$ in the $k$-th iteration.