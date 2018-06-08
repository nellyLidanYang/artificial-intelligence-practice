import numpy as np
np.set_printoptions(threshold=np.inf)
import time

class Solver:
    def __init__(self, input_file="input.txt"):
        with open(input_file) as f:
            line = f.readline().rstrip().split(',')
            self._row, self._col = int(line[0]), int(line[1])

            self.wall_cells = set()
            for _ in xrange(int(f.readline().rstrip())):
                line = f.readline().rstrip().split(',')
                self.wall_cells.add((int(line[0]) - 1) * self._col + int(line[1]) - 1)

            self.terminals = dict()
            for _ in xrange(int(f.readline().rstrip())):
                line = f.readline().rstrip().split(',')
                self.terminals[(int(line[0]) - 1) * self._col + int(line[1]) - 1] = float(line[2])

            line = f.readline().rstrip().split(',')
            self.p_walk, self.p_run = float(line[0]), float(line[1])

            line = f.readline().rstrip().split(',')
            self.r_walk, self.r_run = float(line[0]), float(line[1])

            self.gamma = float(f.readline().rstrip())

            self.actions = ["Walk Up", "Walk Down", "Walk Left", "Walk Right", "Run Up", "Run Down", "Run Left", "Run Right"]

    def init_transition(self):
        self.transition = np.resize(np.arange(self._row * self._col), self._row * self._col*8).reshape(8, self._row * self._col).T
        self.transition[:, 0] += self._col
        self.transition[:, 1] -= self._col
        self.transition[:, 2] -= 1
        self.transition[:, 3] += 1
        self.transition[:, 4] += 2 * self._col
        self.transition[:, 5] -= 2 * self._col
        self.transition[:, 6] -= 2
        self.transition[:, 7] += 2

        # bottom wall
        self.transition[0 : self._col, 1] = np.arange(0, self._col)
        self.transition[0 : self._col, 5] = np.arange(0, self._col)
        if self._row >= 2:
            self.transition[self._col : 2 * self._col, 5] = np.arange(self._col, 2 * self._col)
        # upper wall
        self.transition[self._col * (self._row - 1) : self._col * self._row, 0] = np.arange(self._col * (self._row - 1), self._col * self._row)
        self.transition[self._col * (self._row - 1) : self._col * self._row, 4] = np.arange(self._col * (self._row - 1), self._col * self._row)
        if self._row >= 2:
            self.transition[self._col * (self._row - 2) : self._col * (self._row - 1), 4] = np.arange(self._col * (self._row - 2), self._col * (self._row - 1))
        # left wall
        self.transition[::self._col, 2] = np.arange(0, self._col * self._row, self._col)
        self.transition[::self._col, 6] = np.arange(0, self._col * self._row, self._col)
        self.transition[1::self._col, 6] = np.arange(1, self._col * self._row, self._col)
        # right wall
        self.transition[self._col - 1::self._col, 3] = np.arange(self._col - 1, self._col * self._row, self._col)
        self.transition[self._col - 1::self._col, 7] = np.arange(self._col - 1, self._col * self._row, self._col)
        if self._col >= 2:
            self.transition[self._col - 2::self._col, 7] = np.arange(self._col - 2, self._col * self._row, self._col)

        for wall in self.wall_cells:
            # up cell cant go down
            if wall + self._col < self._row * self._col:
                self.transition[wall + self._col, 1] = wall + self._col
                self.transition[wall + self._col, 5] = wall + self._col
            if wall + 2 * self._col < self._row * self._col:
                self.transition[wall + 2 * self._col, 5] = wall + 2 * self._col
            # down cell cant go up
            if wall - self._col >= 0:
                self.transition[wall - self._col, 0] = wall - self._col
                self.transition[wall - self._col, 4] = wall - self._col
            if wall - 2 * self._col >= 0:
                self.transition[wall - 2 * self._col, 4] = wall - 2 * self._col
            # left cell cant go right
            if wall - 1 >= 0:
                self.transition[wall - 1, 3] = wall - 1
                self.transition[wall - 1, 7] = wall - 1
            if wall - 2 >= 0:
                self.transition[wall - 2, 7] = wall - 2
            # right cell cant go left
            if wall + 1 < self._row * self._col:
                self.transition[wall + 1, 2] = wall + 1
                self.transition[wall + 1, 6] = wall + 1
            if wall + 2 < self._row * self._col:
                self.transition[wall + 2, 6] = wall + 2
            self.transition[wall] = wall

        for terminal in self.terminals:
            self.transition[terminal, :] = np.repeat(terminal, 8)


    def initialize(self):
        p_walk_aside, p_run_aside = 0.5 * (1 - self.p_walk), 0.5 * (1 - self.p_run)
        self.probability = self.gamma * np.array([
            (self.p_walk, 0, p_walk_aside, p_walk_aside, 0, 0, 0, 0),
            (0, self.p_walk, p_walk_aside, p_walk_aside, 0, 0, 0, 0),
            (p_walk_aside, p_walk_aside, self.p_walk, 0, 0, 0, 0, 0),
            (p_walk_aside, p_walk_aside, 0, self.p_walk, 0, 0, 0, 0),
            (0, 0, 0, 0, self.p_run, 0, p_run_aside, p_run_aside),
            (0, 0, 0, 0, 0, self.p_run, p_run_aside, p_run_aside),
            (0, 0, 0, 0, p_run_aside, p_run_aside, self.p_run, 0),
            (0, 0, 0, 0, p_run_aside, p_run_aside, 0, self.p_run) ], dtype=np.float64)

        self.init_transition()

        self.rewards = np.tile(np.array([self.r_walk, self.r_walk, self.r_walk, self.r_walk, self.r_run, self.r_run, self.r_run, self.r_run]),
         self._row * self._col).reshape((self._row * self._col, 8))

        self.U = np.zeros((self._row * self._col, 8))
        self.policy = np.zeros(self._row * self._col)

    def policy_evaluation(self, max_iter=5):
        for _ in xrange(max_iter):
            start = time.time()
            U_prev = self.U.copy()

            self.U = np.dot(self.U, self.probability) + self.rewards
            # update U table
            utility = np.max(self.U, axis=1)

            for terminal in self.terminals:
                utility[terminal] = self.terminals[terminal]
            self.U = utility[self.transition]
            for wall in self.wall_cells:
                self.U[wall, :] = np.zeros(8)
            for terminal in self.terminals:
                self.U[terminal, :] = np.zeros(8)

    def policy_iteration(self, max_iter=1500):
        num_iter = 0
        for _ in xrange(max_iter):
            policy_prev = self.policy.copy()
            self.policy_evaluation()
            self.policy = np.argmax(np.dot(self.U, self.probability) + self.rewards, axis=1)
            if np.array_equal(policy_prev, self.policy):
                break
            num_iter += 1
            print "iter: ", num_iter

    def value_iteration(self, max_iter=5):
        num_iter = 0
        for _ in xrange(max_iter):
            num_iter += 1
            U_prev = self.U.copy()

            self.U = np.dot(self.U, self.probability) + self.rewards
            utility = np.max(self.U, axis=1)
            for terminal in self.terminals:
                utility[terminal] = self.terminals[terminal]
            # update
            self.U = utility[self.transition]
            for wall in self.wall_cells:
                self.U[wall, :] = np.zeros(8)
            for terminal in self.terminals:
                self.U[terminal, :] = np.zeros(8)

            delta = np.max(abs(U_prev - self.U))
            if delta <= epsilon * (1 - self.gamma) / self.gamma:
                break
            print delta, "iter: ", num_iter

            num_iter += 1

    def output_policy(self, output_file="output.txt"): 
        self.initialize()
        self.policy_iteration()
        new_table = np.dot(self.U, self.probability) + self.rewards
        print self.policy[self._col * 20]
        print new_table[self._col * 20]
        print new_table[self._col * 20][7] - new_table[self._col * 20][4]
        self.print_policy(output_file)

    def print_policy(self, output_file):
        self.policy = np.argmax(np.dot(self.U, self.probability) + self.rewards, axis=1)
        with open(output_file, 'w') as f:
            for x in range(self._row)[::-1]:
                tmp = []
                for y in xrange(self._col):
                    cell = x * self._col + y
                    if cell in self.wall_cells:
                        tmp.append('None')
                    elif cell in self.terminals:
                        tmp.append('Exit')
                    else:
                        tmp.append(self.actions[self.policy[cell]])
                f.write(",".join(tmp) + "\n")

a = Solver("input.txt")
a.output_policy("output.txt")