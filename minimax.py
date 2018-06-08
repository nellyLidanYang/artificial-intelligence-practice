class Game:
    def __init__(self, input_file="input.txt"):
        with open(input_file) as f: # try catch
            self._player = f.readline().rstrip()
            if self._player not in ["Star", "Circle"]:
                raise Exception("Invalid Player!")
            self._player = self._player[0]

            self._algo = f.readline().rstrip()
            if self._algo not in ["MINIMAX", "ALPHABETA"]:
                raise Exception("Invalid Algorithum!")

            try:
                self._depth_limit = int(f.readline().rstrip())
            except ValueError as e:
                print "Invalid Depth!", e

            self._chess_board = {}
            self._S_cnt, self._C_cnt = 0, 0
            for row in ["H", "G", "F", "E", "D", "C", "B", "A"]:
                for col, item in enumerate(f.readline().rstrip().split(",")):
                    if item == "0":
                        rock, cnt = 0, 0
                    else:
                        try:
                            rock, cnt = item[0], int(item[1:])
                            if rock == "S":
                                self._S_cnt += 1
                            else:
                                self._C_cnt += 1
                        except ValueError as e:
                            print "Invalid Board State!", e
                    self._chess_board[row + str(col + 1)] = [rock, cnt]

            try:
                self._weight = map(int, f.readline().rstrip().split(","))
            except ValueError as e:
                print "Invalid Weight!", e

        self._node_cnt = 0

        if self._algo == "MINIMAX":
            val, move = self.minimax(self._player, 0, 0)
        else:
            val, move = self.alpha_beta(self._player, 0, 0, -float('inf'), float('inf'))
            
        if move and move != "pass":
            self.move(self._player, move[0], move[1])
            move = move[0] + "-" + move[1]
        opic = self.evaluate_state()

        with open("output.txt", "w") as f:
            f.write(move + "\n" + str(opic) + "\n" + str(val) + "\n" + str(self._node_cnt))

    def opponent(self, player):
        if player == "S":
            return "C"
        return "S"

    def move(self, player, start, end):
        # 1. simple move
        self._chess_board[start] = [0, 0]
        if self._chess_board[end][0] == 0:
            self._chess_board[end] = [player, 1]
        else:
            self._chess_board[end][1] += 1
        # 2. eat opponent
        if abs(ord(start[0]) - ord(end[0])) > 1:
            middle_pos = chr((ord(start[0]) + ord(end[0])) / 2) + str((int(start[1]) + int(end[1])) / 2)
            self._chess_board[middle_pos] = [0, 0]
            if player == "S":
                self._C_cnt -= 1
            else:
                self._S_cnt -= 1
            return True
        return False

    def cancel_move(self, player, start, end, eaten):
        self._chess_board[start] = [player, 1]
        if self._chess_board[end][1] > 1:
            self._chess_board[end][1] -= 1
        else:
            self._chess_board[end] = [0, 0]
        if eaten:
            middle_pos = chr((ord(start[0]) + ord(end[0])) / 2) + str((int(start[1]) + int(end[1])) / 2)
            self._chess_board[middle_pos] = [self.opponent(player), 1]
            if player == "S":
                self._C_cnt += 1
            else:
                self._S_cnt += 1

    def is_game_end(self):
        if not self._S_cnt or not self._C_cnt:
            return True
        return False

    def get_valid_action(self, player):
        def candidate(row, col):
            row = ord(row)
            return [chr(row + 2) + str(col - 1), # 0. left-up-eat
                 chr(row + 2) + str(col + 3), # 1. right-up-eat
                 chr(row + 1) + str(col), # 2. left-up 
                 chr(row + 1) + str(col + 2), # 3. right-up
                 chr(row - 1) + str(col), # 4. left-down
                 chr(row - 1) + str(col + 2), # 5. right-down
                 chr(row - 2) + str(col - 1), # 6. left-down-eat
                 chr(row - 2) + str(col + 3)] # 7. right-down-eat

        actions = []
        for row in ["H", "G", "F", "E", "D", "C", "B", "A"]:
            for col in xrange(8):
                now_pos = row + str(col + 1)
                if self._chess_board[now_pos][0] != player:
                    continue
                candidates = candidate(row, col)
                #print now_pos, candidates
                if player == "S":
                    if candidates[0] in self._chess_board and \
                    (self._chess_board[candidates[0]][0] == 0 or (self._chess_board[candidates[0]][0] == "S" and candidates[0][0] == "H")) and \
                    self._chess_board[candidates[2]][0] == "C":
                        actions.append((now_pos, candidates[0]))
                    if candidates[1] in self._chess_board and \
                    (self._chess_board[candidates[1]][0] == 0 or (self._chess_board[candidates[1]][0] == "S" and candidates[1][0] == "H")) and \
                    self._chess_board[candidates[3]][0] == "C":
                        actions.append((now_pos, candidates[1]))
                    if candidates[2] in self._chess_board and \
                    (self._chess_board[candidates[2]][0] == 0 or (self._chess_board[candidates[2]][0] == "S" and candidates[2][0] == "H")):
                        actions.append((now_pos, candidates[2]))
                    if candidates[3] in self._chess_board and \
                    (self._chess_board[candidates[3]][0] == 0 or (self._chess_board[candidates[3]][0] == "S" and candidates[3][0] == "H")):
                        actions.append((now_pos, candidates[3]))
                else: # player Circle
                    if candidates[4] in self._chess_board and \
                    (self._chess_board[candidates[4]][0] == 0 or (self._chess_board[candidates[4]][0] == "C" and candidates[4][0] == "A")):
                        actions.append((now_pos, candidates[4]))
                    if candidates[5] in self._chess_board and \
                    (self._chess_board[candidates[5]][0] == 0 or (self._chess_board[candidates[5]][0] == "C" and candidates[5][0] == "A")):
                        actions.append((now_pos, candidates[5]))
                    if candidates[6] in self._chess_board and \
                    (self._chess_board[candidates[6]][0] == 0 or (self._chess_board[candidates[6]][0] == "C" and candidates[6][0] == "A")) and \
                    self._chess_board[candidates[4]][0] == "S":
                        actions.append((now_pos, candidates[6]))
                    if candidates[7] in self._chess_board and \
                    (self._chess_board[candidates[7]][0] == 0 or (self._chess_board[candidates[7]][0] == "C" and candidates[7][0] == "A")) and \
                    self._chess_board[candidates[5]][0] == "S":
                        actions.append((now_pos, candidates[7]))
        return actions

    def evaluate_state(self):
        total = 0
        for row in xrange(8):
            for col in xrange(1, 9):
                if self._chess_board[chr(row + ord('A')) + str(col)][0] == "S":
                    total += self._weight[row] * self._chess_board[chr(row + ord('A')) + str(col)][1]
                elif self._chess_board[chr(row + ord('A')) + str(col)][0] == 0:
                    pass
                else:
                    total -= self._weight[7 - row] * self._chess_board[chr(row + ord('A')) + str(col)][1]
        if self._player == "C":
            return -total
        return total


    def minimax(self, player, depth, passed):
        self._node_cnt += 1
        if depth >= self._depth_limit:
            # return evaluation result
            return self.evaluate_state(), None

        """
        exit, leaf node
        """
        # 1. both pass
        if passed == 2:
            return self.evaluate_state(), None

        best, bestMove = -float('inf'), None
        if player != self._player:
            best = -best
        
        valid_actions = self.get_valid_action(player)
        
        """
        exit, leaf node
        """
        # 2. only one player's rock(s)
        if self.is_game_end():
            return self.evaluate_state(), None

        """
        expansion
        """
        #pass
        if not valid_actions:
            return self.minimax(self.opponent(player), depth + 1, passed + 1)[0], "pass"

        if player == self._player:
            for start, end in valid_actions:
                eaten = self.move(player, start, end)
                val, _ = self.minimax(self.opponent(player), depth + 1, 0)
                if val > best:
                    best, bestMove = val, (start, end)
                # recover
                self.cancel_move(player, start, end, eaten)
        else:
            for start, end in valid_actions:
                eaten = self.move(player, start, end)
                val, _ = self.minimax(self.opponent(player), depth + 1, 0)
                if val < best:
                    best, bestMove = val, (start, end)
                # recover
                self.cancel_move(player, start, end, eaten)
        # upload value to parent node
        return best, bestMove

    def alpha_beta(self, player, depth, passed, alpha, beta):
        self._node_cnt += 1
        if depth >= self._depth_limit:
            # return evaluation result
            return self.evaluate_state(), None

        """
        exit, leaf node
        """
        # 1. both pass
        if passed == 2:
            return self.evaluate_state(), None

        best, bestMove = -float('inf'), None
        if player != self._player:
            best = -best
        
        valid_actions = self.get_valid_action(player)
        
        """
        exit, leaf node
        """
        # 2. only one player's rock(s)
        if self.is_game_end():
            return self.evaluate_state(), None

        """
        expansion
        """
        #pass
        if not valid_actions:
            return self.alpha_beta(self.opponent(player), depth + 1, passed + 1, alpha, beta)[0], "pass"

        if player == self._player:
            for start, end in valid_actions:
                eaten = self.move(player, start, end)
                val, _ = self.alpha_beta(self.opponent(player), depth + 1, 0, alpha, beta)
                # recover
                self.cancel_move(player, start, end, eaten)
                if val > best:
                    best, bestMove = val, (start, end)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
        else:
            for start, end in valid_actions:
                eaten = self.move(player, start, end)
                val, _ = self.alpha_beta(self.opponent(player), depth + 1, 0, alpha, beta)
                # recover
                self.cancel_move(player, start, end, eaten)
                if val < best:
                    best, bestMove = val, (start, end)
                beta = min(beta, val)
                if beta <= alpha:
                    break

        # upload value to parent node
        return best, bestMove


game = Game("input.txt")