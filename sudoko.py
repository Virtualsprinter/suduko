# Non-optimal Sudoko solver originally developed on a terrace in Rome May 2015
oneinthree = {(0,1):2,(0,2):1,(1,2):0,
              (3,4):5,(3,5):4,(4,5):3,
              (6,7):8,(6,8):7,(7,8):6}

complete = [1,2,3,4,5,6,7,8,9]
complete0 = [0,1,2,3,4,5,6,7,8]

m = \
    [[6,0,0,0,0,0,0,0,0],
     [0,0,8,0,0,7,9,0,0],
     [0,1,4,0,8,5,0,0,0],
     [0,0,0,0,6,0,0,0,0],
     [0,7,0,0,0,0,1,0,2],
     [0,9,0,1,0,2,0,0,5],
     [0,0,2,0,0,9,0,3,0],
     [0,0,0,0,1,4,0,8,0],
     [0,3,0,0,0,0,0,0,1]]


class sudoko(object):

    def __init__(self, m):
        #print "sudoko constructor"
        # candidates are a list of candidate for each cell
        # m is the sudoko matrix with an entry of zero for each unsolved cell
        self.__candidates = []
        self.__m = m


    def __create_candidates(self):
        # Find candidates for a cell given the information in the row
        rix = 0
        for row in self.__m:
            cix = 0
            self.__candidates.append([])
            for e in row:
                self.__candidates[rix].append([])
                if e == 0:
                    for i in complete:
                        if i not in row:
                            self.__candidates[rix][cix].append(i)
                cix += 1
            rix +=1


    def __print_candidates(self):
        k = 1
        for r in self.__candidates:
            print k, "(1,2,3):" , r[0], r[1], r[2]
            print k, "(4,5,6):" , r[3], r[4], r[5]
            print k, "(7,8,9):" , r[6], r[7], r[8]
            k += 1


    def __print_matrix(self):
        for row in self.__m:
            print row


    def __clean(self, rix, cix):
        # to be called after solving a cell
        # to remove candidates in same square, row and column
        value = self.__m[rix][cix]
        for row in complete0:
            if value in self.__candidates[row][cix]:
                self.__candidates[row][cix].remove(value)
        for col in complete0:
            if value in self.__candidates[rix][col]:
                self.__candidates[rix][col].remove(value)

        ri = 3*(rix/3)
        ci = 3*(cix/3)
        for r in [ri, ri+1, ri+2]:
            for c in [ci, ci+1, ci+2]:
                if value in self.__candidates[r][c]:
                    self.__candidates[r][c].remove(value)


    def __solved(self, rix, cix, solution, text):
        self.__m[rix][cix] = solution
        # remove all candidates from this cell
        self.__candidates[rix][cix]=[]
        print "Solved",text,":", rix+1, cix+1, ":",  self.__m[rix][cix]
        self.__solvedsomething = True
        self.__clean(rix, cix)


    def __rowandcolumnelimination(self):
        # Reduce candidates based on what is available in columns
        for row in complete0:
            for col in complete0:
                if self.__m[row][col] != 0:
                    # the cell is solved
                    for r in complete0:
                        # remove candidates in same column
                        if self.__m[row][col] in self.__candidates[r][col]:
                            self.__candidates[r][col].remove(self.__m[row][col])
                            if len(self.__candidates[r][col]) == 1:
                                self.__solved(r,col, self.__candidates[r][col][0],\
                                            "row and column elimination")
                col += 1
            row += 1

    def __rowelimination(self):
        # Reduce candidates based on what is available in rows
        for row in complete0:
            for col in complete0:
                if self.__m[row][col] == 0:
                    solved = False
                    for i in self.__candidates[row][col]:
                        for c in complete0:
                            if i in self.__candidates[row][c] and c != col:
                                break
                        else:
                            # Only one cell in this row has this candidate
                            self.__candidates[row][col] = [i]
                            self.__solved(row, col, self.__candidates[row][col][0],\
                                            "row elimination")
                            solved = True
                        if solved is True:
                            break
                col += 1
            row += 1

    def __columnelimination(self):
        # Reduce candidates based on what is available in columns
        for col in complete0:
            for row in complete0:
                if self.__m[row][col] == 0:
                    solved = False
                    for i in self.__candidates[row][col]:
                        for r in complete0:
                            if i in self.__candidates[r][col] and r != row:
                                break
                        else:
                            # Only one cell in this column has this candidate
                            #self.__print_matrix()
                            #print "Remove candidate in:", row, col
                            self.__candidates[row][col] = [i]
                            self.__solved(row, col, self.__candidates[row][col][0],\
                                            "column elimination")
                            #self.__print_candidates()
                            solved = True
                        if solved is True:
                            break
                row += 1
            col += 1

    def __squareelimination(self):
        # Reduce candidates based on what is available in squares
        for row in complete0:
            for col in complete0:
                if self.__m[row][col] != 0:
                    # the cell is solved
                    # check if we can remove candidates in the cells square
                    ri = 3*(row/3)
                    ci = 3*(col/3)
                    for r in [ri, ri+1, ri+2]:
                        for c in [ci, ci+1, ci+2]:
                            if r == row and c == col:
                                continue
                            if self.__m[row][col] in self.__candidates[r][c]:
                                self.__candidates[r][c].remove(self.__m[row][col])
                                if len(self.__candidates[r][c]) == 1:
                                    self.__solved(r,c, self.__candidates[r][c][0],\
                                                "square elimination")
                col += 1
            row += 1


    def __squaresinglecandidate(self):
        # Look for candidates that are the only alternative in a square
        rix = 0
        for row in self.__m:
            cix = 0
            for e in row:
                if e == 0:
                    l = self.__candidates[rix][cix]
                    for i in l:
                        ri = 3*(rix/3)
                        ci = 3*(cix/3)
                        inst = 0
                        for r in [ri, ri+1, ri+2]:
                            for c in [ci, ci+1, ci+2]:
                                if i in self.__candidates[r][c]:
                                    inst += 1
                        if inst == 1:
                            self.__solved(rix,cix,i,"only candidate in square")
                            break
                cix += 1
            rix += 1


    def __blocking(self):
        # Look for rows or columns that locks a number in a square row or column
        # Then look for squares that can utilize this
        rix = 0
        for row in self.__m:
            cix = 0
            for e in row:
                if e == 0:
                    # For each unsolved element
                    candidates = self.__candidates[rix][cix]
                    if len (candidates) == 1:
                        self.__solved(rix,cix, self.__candidates[rix][cix][0],\
                                    "only option left in cell")
                        continue
                    for i in candidates:
                        # find the local square
                        ri = 3*(rix/3)
                        ci = 3*(cix/3)
                        block = []
                        # Collect all local cells with same candidate i
                        for r in [ri, ri+1, ri+2]:
                            for c in [ci, ci+1, ci+2]:
                                if i in self.__candidates[r][c]:
                                    block.append([r,c])
                        first = True
                        samecol = True
                        samerow = True
                        # Check if local cells only exist in same row or column
                        for co in block:
                            if first:
                                fr = co[0]
                                fc = co[1]
                                first = False
                            else:
                                if fr != co[0]:
                                    samerow = False
                                if fc != co[1]:
                                    samecol = False
                        if len(block) == 0:
                            continue
                        # if same row or col remove candidates in other squares
                        # other rows or columns
                        if samerow == True:
                            for rc in complete0:
                                if rc in [ci, ci+1, ci+2]:
                                    continue
                                if i in self.__candidates[fr][rc]:
                                    # Remove this candidate in other squares column same row
                                    self.__candidates[fr][rc].remove(i)
                                    self.__solvedsomething = True
                                    if len (self.__candidates[fr][rc]) == 1:
                                        self.__solved(fr, rc,\
                                            self.__candidates[fr][rc][0],\
                                            "blocking from other square on row")
                        if samecol == True:
                            for rr in complete0:
                                if rr in [ri, ri+1, ri+2]:
                                    continue
                                if i in self.__candidates[rr][fc]:
                                    # Remove this candidate in other squares row same column
                                    self.__candidates[rr][fc].remove(i)
                                    self.__solvedsomething = True
                                    if len (self.__candidates[rr][fc]) == 1:
                                        self.__solved(rr, fc,\
                                            self.__candidates[rr][fc][0],\
                                            "blocking from other square on column")
                cix += 1
            rix += 1

    def __lock(self):
        # For each column check if 2 rows in a square lock a candidate
        # "Austins Challenge"
        for cix in complete0:
            for rix in complete0:
                candidates = self.__candidates[rix][cix]
                for i in candidates:
                    lock = []
                    for ro in complete0:
                        if i in self.__candidates[ro][cix]:
                            lock.append(ro)
                    # Check if only two and in same column and square
                    if len(lock) == 2:
                        if lock[0]/3 == lock[1]/3:
                            # Found two in same column and square
                            lock.sort()
                            row = oneinthree[tuple(lock)]
                            for c in complete0:
                                if c/3 == cix/3:
                                    if i in self.__candidates[row][c]:
                                        self.__candidates[row][c].remove(i)
                                        self.__solvedsomething = True
                                        print "Lock row removal", row, c, i

                candidates = self.__candidates[rix][cix]
                for i in candidates:
                    lock = []
                    for co in complete0:
                        if i in self.__candidates[rix][co]:
                            lock.append(co)
                    # Check if only two and in same row and square
                    if len(lock) == 2:
                        if lock[0]/3 == lock[1]/3:
                            # Found two in same row and square
                            lock.sort()
                            column = oneinthree[tuple(lock)]
                            for r in complete0:
                                if r/3 == rix/3:
                                    if i in self.__candidates[r][column]:
                                        self.__candidates[r][column].remove(i)
                                        self.__solvedsomething = True
                                        print "Lock column removal", r, column, i

    def __cellsleft(self):
        remaining = 0
        for row in complete0:
            for col in complete0:
                if self.__m[row][col] == 0:
                    remaining += 1
        return remaining


    def solve(self):
        # Solve Sudoko
        from datetime import datetime
        start = datetime.now()
        self.__create_candidates()
        cnt = 0
        self.__solvedsomething = True
        while self.__solvedsomething:
            self.__solvedsomething = False
            cnt += 1
            print "iteration:", cnt
            self.__rowandcolumnelimination()
            self.__rowelimination()
            self.__columnelimination()
            self.__squareelimination()
            self.__squaresinglecandidate()
            self.__blocking()
            self.__lock()
            remaining = self.__cellsleft()
            print "Remaining cells:", remaining
            if remaining == 0:
                break

        stop = datetime.now()
        if remaining != 0:
            print "Failed to solve Sudoko", cnt, "iteration(s) in", stop-start
            self.__print_candidates()
            self.__print_matrix()
        else:
            print "Solved Sudoko using", cnt, "iteration(s) in", stop-start

    def printit(self):
        self.__print_matrix()


    def solution(self):
        return self.__m

# Todo check input, correctness of solution, gui, optimize
import sys

def main(argv):
    s = sudoko(m)
    s.solve()
    s.printit()

if __name__ == '__main__':
    main(sys.argv)
