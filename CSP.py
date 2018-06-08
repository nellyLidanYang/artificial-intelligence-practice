import copy

class Solver:
    def __init__(self, input_file="input.txt"):
        self.MAX_TEAM = 32
        with open(input_file) as f:
            self._num_group = int(f.readline().rstrip())
            self._num_pot = int(f.readline().rstrip())

            "variables are countries mentioned"
            self._vars = {}
            self.neighbors = {}
            initial_assignment = {}


            pot_max_cnt = 0
            pot_0 = None
            for pot_idx in xrange(self._num_pot):
                line = f.readline().rstrip().split(',')
                for item in line:
                    self._vars[item] = [pot_idx, None]
                for item in line:
                    self.neighbors[item] = set([_ for _ in line if _ != item])
   
                
                if pot_idx == 0:
                    pot_0 = line

                pot_max_cnt = max(pot_max_cnt, len(line))

            if pot_max_cnt > self._num_group:
                self.write_output()
                return

            line = f.readline()
            confederation_max_cnt = 0
            UEFA = 0
            while line:
                clean_line = line.rstrip()
                confederation, clean_line = clean_line.split(':')
                if clean_line == "None":
                    line = f.readline()
                    continue
                clean_line = clean_line.split(',')
                for country in clean_line:
                    self._vars[country][1] = confederation
                    if confederation != "UEFA":
                        for cc in clean_line:
                            if cc != country:
                                self.neighbors[country].add(cc)
                if confederation == "UEFA":
                    self.UEFA_teams = set(clean_line)
                    UEFA = len(self.UEFA_teams)
                else:
                    confederation_max_cnt = max(confederation_max_cnt, len(clean_line))
                line = f.readline()

        self.UEFA_cnt = {_ : 0 for _ in xrange(self._num_group)}
        self.now_domain = {_ : {i : 1 for i in xrange(self._num_group)} for _ in self._vars}

        "initial assignment: the first team in each pot must be in different groups."
        for idx, item in enumerate(pot_0):
            self.assign(initial_assignment, item, idx)

        if confederation_max_cnt > self._num_group or UEFA > self._num_group * 2:
            self.write_output()
            return

        # start searching
        assignment = self.dfs_search(initial_assignment)
        self.write_output(assignment)

    def write_output(self, assignment=None):
        with open("output.txt", 'w') as f:
            if assignment is None:
                f.write("No")
            else:
                f.write("Yes\n")
                groups = [[] for _ in xrange(self._num_group)]

                for team, group in assignment.items():
                    groups[group].append(team)
                for _ in xrange(self._num_group):
                    if _ == (self._num_group - 1):
                        if len(groups[_]) == 0:
                            f.write("None")
                        else:
                            f.write(",".join(groups[_]))
                    else:
                        if len(groups[_]) == 0:
                            f.write("None\n")
                        else:
                            f.write(",".join(groups[_]) + "\n")


    def assign(self, assignment, x, val):
        assignment[x] = val
        self.now_domain[x] = {val : 1}
        if self._vars[x][1] == "UEFA":
            self.UEFA_cnt[val] += 1
        "do forward check"
        # remove val from domain of all uefa team (as urnary)
        if self._vars[x][1] == "UEFA" and self.UEFA_cnt[val] == 2:
            for team in [_ for _ in self.UEFA_teams if _ not in assignment and _ != x]:
                if val in self.now_domain[team]:
                    del self.now_domain[team][val]
                    if len(self.now_domain[team]) == 0:
                        return False

        for neigh in [_ for _ in self.neighbors[x] if _ not in assignment]:
            neigh_domain = self.now_domain[neigh].keys()
            for val2 in neigh_domain:
                if self.is_conflict_value(x, val, neigh, val2):
                    del self.now_domain[neigh][val2]
            if len(self.now_domain[neigh]) == 0:
                return False
        return True

    def is_conflict_value(self, x1, v1, x2, v2):
        "check if x1=v1 and x2=v2 conflict with each other."
        if v1 != v2:
            return False
        if self._vars[x1][0] == self._vars[x2][0] or (self._vars[x1][1] != "UEFA" and self._vars[x1][1] == self._vars[x2][1]):
            return True
        if self._vars[x1][1] == "UEFA" and self._vars[x1][1] == self._vars[x2][1]:
            if self.UEFA_cnt[self._vars[x1][0]] > 0:
                return True
        return False

    def minimum_remaining_variable(self, assignment):
        # if no candidate?
        candidates = [_ for _ in self._vars if _ not in assignment]
        candidates.sort(key = lambda _ : len(self.now_domain[_]))
        return candidates[0]

    def dfs_search(self, assignment):
        if len(assignment) == len(self._vars):
            return assignment

        unassigned_var = self.minimum_remaining_variable(assignment)
        
        old_now_domain = copy.deepcopy(self.now_domain)

        unassigned_var_domain = self.now_domain[unassigned_var].keys()
        for val in unassigned_var_domain:
            if val not in self.now_domain[unassigned_var]:
                continue
            
            # keep arc consistency, do forward checking
            assign_status = self.assign(assignment, unassigned_var, val)
            if assign_status:
                solution = self.dfs_search(assignment)
                "stop when find a solution"
                if solution is not None:
                    return solution

            # unassign, restore
            del assignment[unassigned_var]
            self.now_domain = copy.deepcopy(old_now_domain)
            if self._vars[unassigned_var][1] == "UEFA":
                self.UEFA_cnt[val] -= 1

        return None

a = Solver("input8.txt")