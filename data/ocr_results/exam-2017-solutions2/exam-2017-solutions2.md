# Final Exam 

600.435 Artificial Intelligence<br>Spring $2017$

## 1. Name:

## 2. Instructions

- Please be sure to write both your name and section in the space above!
- Please be sure to read through the entire exam before you start, and be mindful of the time. If one question is taking too long, it may be worth moving on and coming back to the problem question(s) after the rest of the exam is complete.
- Remember that you are only allowed one sheet (both sides) of notes, everything else besides that and the test itself must be off of your workspace.
- Please show ALL relevant work for your answers and provide explanations when prompted. Failure to do either will result in loss of credit.
- You will have until $5$ pm to complete this test.

1. (8 points) Consider a self-driving car as an intelligent agent. Name two items for each of the PEAS elements.

- Performance measures:
- Environment:

$$
\begin{aligned}
& \text { res: } \\
& \text { speed to reach goal } \\
& \text { accident avoidane }
\end{aligned}
$$

$$
\begin{aligned}
& \text { traffic (other ares) } \\
& \text { road }
\end{aligned}
$$

- Actuators:

$$
\begin{aligned}
& \text { motor (acellestor) } \\
& \text { steer is }
\end{aligned}
$$

- Sensors:

$$
\begin{array}{ll}
\text { speedometer cave } \\
\text { GPS lidar }
\end{array}
$$

2. (5 points) Consider a computer program that is playing online poker.

Is the environment of this intelligent agent ...

- Fully observable?
no
- Deterministic?
no
- Static?
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-2.jpg?height=85&width=98&top_left_y=1508&top_left_x=550)
- Discrete?
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-2.jpg?height=101&width=115&top_left_y=1668&top_left_x=547)

In which of these categories is a Go playing program different?

## 3. determinate

Just provide a yes/no answer to each of these questions.

In the following grid, we want to find the fastest path from $\mathbf{A}$ to $\mathbf{G}$.
We may move from every cell to each directly neighboring cell (up, down, left, right).
The cell in the center of the grid is unreachable.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-3.jpg?height=608&width=608&top_left_y=471&top_left_x=783)
3. (7 points) Draw the full search tree of breadth-first search that explores this grid.

- Note that search may return to already visited cells.
- The search graph must include all leaf nodes at maximum depth.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-3.jpg?height=533&width=590&top_left_y=1368&top_left_x=594)

4. (3 points) If we use depth-first search and move

- up, whenever possible
- right, whenever possible (and up is not possible)
- down, whenever possible (and up and right is not possible)
- left, otherwise

Again, search may return to already visited cells.
Will depth-first succeed? If yes, in how many steps? If no, why not?

$$
A \rightarrow b \rightarrow c \rightarrow e
$$

Consider the search space below, where $\mathbf{S}$ is the start node and $\mathbf{G 1}$ and $\mathbf{G 2}$ satisfy the goal test. Arcs are labeled with the cost of traversing them and the heuristic cost to a goal is reported inside nodes (so lower scores are better).
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-4.jpg?height=711&width=1235&top_left_y=433&top_left_x=472)
5. (10 points) For A* search, indicate which goal state is reached at what cost and list, in order, all the states popped off of the OPEN list. You use a search graph to show your work.
Note: When all else is equal, nodes should be removed from OPEN in alphabetical order.

Path to goal (cost):

States popped off of OPEN:
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-4.jpg?height=1231&width=1811&top_left_y=1521&top_left_x=0)

## 4. Game Playing

![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-5.jpg?height=219&width=545&top_left_y=0&top_left_x=958)

Apply the mini-max algorithm to the partial game tree below, where it is the minimizer's turn to play and the game does not involve randomness. The values estimated by the static-board evaluator (SBE) are indicated in the leaf nodes (higher scores are better for the maximizer).

Process this game tree working left-to-right.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-5.jpg?height=724&width=1636&top_left_y=527&top_left_x=326)
6. (5 points) Write the estimated values of the intermediate nodes inside their circles.
7. (2 points) Indicate the proper move of the minimizer by circling one of the root's outgoing arcs.
8. (5 points) Circle each leaf node (if any) whose SBE score does not need to be consulted.

Briefly explain why:
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-5.jpg?height=397&width=1432&top_left_y=1761&top_left_x=482)
9. (5 points) Convert the following sentence into first-order predicate calculus logic: There is a lacrosse player who has played in every game this season.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-6.jpg?height=269&width=1820&top_left_y=356&top_left_x=212)
10. (10 points) Given the following propositional-logic clauses, show $E$ must be true by adding $\neg E$ and using only the resolution inference rule to derive a contradiction.
Use the notation presented in class (and in the book) where the resulting clause is connected by lines to the two clauses resolved.

- $A \vee \neg C$
- $B \vee \neg A$
- $B \vee \neg D$
- $E \vee \neg A \vee \neg B$
- $C$
- $\neg D$
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-6.jpg?height=751&width=562&top_left_y=1164&top_left_x=955)

11. (5 points) Suppose we roll a die $2$ times. What is the probability that the sum of the numbers is $3$ ?
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-7.jpg?height=418&width=1970&top_left_y=371&top_left_x=65)
12. ( $5$ points) In the general population, $0.1 \%$ have the disease X .

Doctors developed a test with the following properties:

- If a person has the disease, the test detects it $90 \%$ of the time, and fails to detect it in $10 \%$ of the time.
- If a person does not have the disease, the test gives false positive indication $10 \%$ of the time, and a correct negative indication $90 \%$ of the time.

What is the probability that a random person who receives a positive test result, does indeed have the disease (round numbers when appropriate)?

$$
\begin{aligned}
p(T \mid D) & =0.9 \quad p(D)=0.001 \\
p(T / \sim D) & =0.1 \\
p(D \mid T) & =\frac{p(T \mid D) p(D)}{P(T)} \\
& \left.=\frac{p(T \mid D) p(D)}{p(T \mid D) p(D)+p(T)} 1 / D\right) p(\neg D) \\
& =.9 \times .001 \\
.9 \times .001+.1 \times .999 & \approx \frac{.9}{1.00}
\end{aligned}
$$

Consider the following Bayesian Network, where variables A-D are all Boolean valued (when answering the questions be sure to show your work, if a computation gets too convoluted it's fine just state terms with numbers):
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-8.jpg?height=443&width=985&top_left_y=391&top_left_x=597)

| $\mathbf{A}$ | $\mathbf{B}$ | $\mathbf{P}(\mathbf{C}=$ true $\mid \mathbf{A}, \mathbf{B})$ |
| :---: | :---: | :---: |
| false | false | $0.2$ |
| false | true | $0.3$ |
| true | false | $0.1$ |
| true | true | $0.6$ |


| $\mathbf{B}$ | $\mathbf{C}$ | $\mathbf{P}(\mathbf{D}=$ true $\mid \mathbf{B}, \mathbf{C})$ |
| :---: | :---: | :---: |
| false | false | $0.9$ |
| false | true | $0.8$ |
| true | false | $0.4$ |
| true | true | $0.3$ |

13. (5 points) What is the probability that all four of these Boolean variables are false?

$$
\begin{aligned}
& p(\neg A) p(\neg B) p(\neg C \mid \neg A \rightarrow A) p(\neg D \mapsto B, \supset C) \\
= & .8 \times .3 \times .8 \times .1=0 Q 2
\end{aligned}
$$

14. (5 points) What is the probability that $\mathbf{A}$ is true, $\mathbf{C}$ is true and $\mathbf{D}$ is false?

$$
p(A, C, P)=p(A, B, C, D)+p(A, B, C>D)
$$
15. (5 points) What is the probability that $\mathbf{A}$ is true given that $\mathbf{C}$ is the and $\mathbf{D}$ is false?
\$\$\begin{aligned}

\& P(A \mid C, \rightarrow D)=\frac{P(A, C, D D)}{P(C, \neg D)}= <br>
\& =\frac{P(A, C, D D)}{P(A, C, \neg D)+P(\neg A, C, \neg D)} <br>
\& =\frac{.06(1)}{.06+P(\neg A, C, \neg D)}=···=\frac{.06}{.06+.127}

\end{aligned}\$\$

Consider the deterministic reinforcement environment drawn below, where the current state of the Q table is indicated on the arcs. Let $\gamma=1$. Immediate rewards are indicated inside nodes. Once the agent reaches the end state the current episode ends.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-9.jpg?height=396&width=917&top_left_y=344&top_left_x=631)
16. (5 points) Assuming our RL agent exploits its policy (with learning turned off), what is the path it will take from start to end? Briefly explain your answer.

$$
f_{a} \rightarrow b \rightarrow c \rightarrow e u d
$$
17. (5 points) Assuming the RL agent is using one-step Q learning and moves from node start to node $\mathbf{b}$. Report below the changes to the graph above (only display what changes). Assume a learning rate of $\alpha=1$. Show your work.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-9.jpg?height=747&width=1515&top_left_y=1342&top_left_x=609)
18. (5 points) Show the final state of the Q table after a very large number of training episodes (ie., show the Q table where the Bellman Equation is satisfied everywhere). No need to show your work nor explain your answer.
![](https://cdn.mathpix.com/cropped/2025_04_29_5d79eb8f853b8e4b4501g-9.jpg?height=324&width=925&top_left_y=2283&top_left_x=573)

