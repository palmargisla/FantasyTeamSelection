# FantasyTeamSelection

Being surrounded by football enthusiasts, there is no getting around playing the Fantasy football game.  
Therefore I thought it might be interesting to pick my team mostly based on data, such that the expected points are maximized.

## About Fantasy football

For those not familiar with Fantasy football, as described on wikipedia

> Fantasy football is a game in which participants assemble an imaginary team of real life football players and score points based on those players' actual statistical performance or their perceived contribution on the field of play.

You start with a budget of £100, and you are suppost to assemble a team of 15 players, that fit within the given criteria:

* No more than 3 players from each team.
* Should include 2 goalkeepers, 5 defenders, 5 midfielders and 3 forwards.

## Results

To solve the problem, I thought this would be a great oportunity to try out the package `pulp`, as that package includes as Integer Linear Program solver. 

The file `helpers.py` is the base for the project, containing both the extraction of data from a html file and the optimization formulation. 

There are two notebooks in this project, the first one is `GW1-initial.ipynb` which shows the results for the initial squad selection. The second notebook is `GW4-wildcard.ipynb` which shows the results from gw4, where I used my wildcard.